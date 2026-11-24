# C.U.T.Y. — FIR digital: seguimiento PAN y voz

Estado: filtros integrados en código C y Python; el FIR de voz se desactiva por defecto. El flujo de seguimiento PAN llega por UART al firmware perfilado y este genera PWM cuando se habilita físicamente. Los builds/tests de software no son mediciones físicas; faltan calibración y validación del servo, y no hay comparación de reconocimiento de voz con el FIR activado. Las gráficas de la web son cálculos sobre señales sintéticas.

## Señales y límites de integración

El tracker actual suaviza detecciones con EMA `detection_alpha=0.35`, filtra la derivada del PID con `derivative_alpha=0.25`, usa banda muerta y límites de aceleración/velocidad. En simulación no escribe UART; en modo físico, el adaptador de seguimiento manda objetivos limitados por socket al único dueño UART de Raspberry. STM32 acepta objetivos V2 y `ServoControlTask` invoca `cuty_control_tick` cada 20 ms nominales (50 Hz), con supervisión cada 10 ms. La trayectoria ya limita velocidad y aceleración. El pasa-bajas actúa sobre HEAD_PAN en ese tick; los dos brazos conservan su trayectoria y las cinco salidas de PCB permanecen intactas.

Así, los 40 ms de retardo FIR son adicionales al suavizado EMA, la dinámica del controlador de Pi y la trayectoria STM32. Esos retardos anteriores dependen de la tasa de cámara y de su dinámica; no se pueden resumir honestamente en un número sin medir la ruta completa. El filtro web ilustra solamente la media móvil y una variación sintética de referencia.

La captura existente entrega PCM16 little-endian, mono, en bloques de 20 ms. `app.py` selecciona 16 kHz para Gemini Live (`audio/pcm;rate=16000`) y 24 kHz para OpenAI Realtime. Se usa esa misma tasa seleccionada para diseñar los coeficientes; la ruta común de `ConversationService` procesa exclusivamente bloques entrantes del micrófono antes de `provider.send_audio`. La salida del modelo, reproducción, música, half-duplex, captura de cámara y dispositivos no pasan por el filtro.

## FIR pasa-bajas de posición PAN

Módulo `stm32/App/control/fir_filter.c/.h`, integrado en `body_control.c`. Coeficientes `h=[0.2,0.2,0.2,0.2,0.2]`, longitud `N=5`, orden `4`, muestreo nominal 50 Hz. Buffer circular fijo, sin asignación dinámica; validación de punteros, número de taps y valores finitos. El acumulador también debe ser finito.

Ecuación en diferencias:

`y[n] = 0.2(x[n] + x[n−1] + x[n−2] + x[n−3] + x[n−4])`.

Impulso: `[0.2,0.2,0.2,0.2,0.2]`. Para un escalón unitario con historial cero: `[0.2,0.4,0.6,0.8,1,1,…]`. Una entrada constante `c` después del arranque produce `c`; ganancia DC unitaria y sin deriva de acumulación. FIR causal, simétrico, fase lineal; retardo de grupo `(N−1)/2=2 muestras=40 ms`. Estable: es FIR con suma absoluta finita de coeficientes (=1).

Respuesta compleja:

`H(e^{jω}) = e^{−j2ω} [sin(5ω/2)/(5 sin(ω/2))]`, con `ω=2πf/50`; en los ceros la fase salta π. Valores calculados para magnitud (fase lineal −2ω módulo los saltos):

| f (Hz) | |H| | Magnitud (dB) |
|---:|---:|---:|
| 0 | 1.000 | 0.00 |
| 2 | 0.938 | −0.56 |
| 5 | 0.647 | −3.78 |
| 10 | 0 | −∞ (cero ideal) |
| 15 | 0.247 | −12.14 |
| 20 | 0 | −∞ (cero ideal) |

Complejidad por muestra: 5 multiplicaciones y 4 sumas, 250 multiplicaciones/s y 200 sumas/s a 50 Hz, además de coste fijo de buffer. No usa punto flotante en ISR; corre en tarea STM32.

### A/B y seguridad

`cuty_control_set_head_fir(controller, enabled)` cambia el modo desde el dueño serializado del controlador. Al cambiarlo, llena el historial con el objetivo PAN actual; las muestras viejas no reaparecen y activar el FIR no inserta un paso inicial. Al salir de ACTIVE, se reinicia al objetivo comandado y la política de seguridad congela la trayectoria existente. El filtro no habilita el driver PWM. La configuración inicial del módulo de control lo deja activo en la lógica portable; para A/B se llama explícitamente al setter. No hay comando V2 para cambiarlo durante una sesión física.

## FIR pasa-banda de audio

Módulo `raspberry/src/cuty/audio/speech_bandpass.py`; solo PCM16 entrante. Diseño reproducible de ventana Hamming sobre la respuesta ideal diferencia de dos pasa-bajas, longitud impar `N=511`, orden 510, simétrico, normalizado a ganancia 1 en el centro de banda (2,075 Hz). Se eligió 511 frente a 127 taps al medir −45 dB vs −10.6 dB a 100 Hz a 16 kHz, con retardo nominal de 15.94 ms. Frecuencias de corte nominales 150–4,000 Hz y se validan estrictamente por debajo de Nyquist. A 16 kHz (Gemini) y 24 kHz (OpenAI) Nyquist es respectivamente 8 y 12 kHz. 4 kHz conserva una fracción importante de consonantes e inteligibilidad, mientras atenúa subgrave y ultrasonido; 150 Hz se trata como transición ancha, no como corte abrupto. La respuesta real lista abajo muestra que 150 Hz ya está a −6 dB. No se afirma que este ajuste mejore ASR.

`h[k] = (h_ideal,high[k] − h_ideal,low[k]) · w_Hamming[k]`, luego normalizar `|H(f_center)|=1`; `y[n]=Σ(k=0…510) h[k]x[n−k]`. La respuesta al impulso es la lista completa de coeficientes generada por `design_bandpass`; es simétrica. El escalón converge a cero porque `H(0)=0` idealmente (restos numéricos de redondeo). FIR causal de fase lineal, retardo de grupo 255 muestras: 15.9375 ms a 16 kHz o 10.625 ms a 24 kHz. BIBO estable porque la suma absoluta de 511 coeficientes es finita. La implementación usa NumPy, ya incluido en `raspberry/requirements.txt`, para convolución vectorizada por bloques y canales. Coste aproximado: 511 MAC/muestra = 8.176 M MAC/s a 16 kHz y 12.264 M MAC/s a 24 kHz. Medición informativa local (Windows/CPython, 100 bloques de 20 ms): 0.032 ms/bloque a 16 kHz y 0.037 ms/bloque a 24 kHz. No representa la Raspberry Pi; medir CPU y duración por bloque en la Pi antes de habilitar.

Respuesta del diseño actual (cálculo DFT de coeficientes, valores redondeados; amplitud normalizada a 2,075 Hz):

| Frecuencia | 16 kHz | 24 kHz |
|---:|---:|---:|
| 50 Hz | −68.2 dB | −59.5 dB |
| 100 Hz | −45.1 dB | −23.9 dB |
| 150 Hz | −6.0 dB | −6.0 dB |
| 250 Hz | ≈0 dB | 0 dB |
| 500 Hz | ≈0 dB | ≈0 dB |
| 1 kHz | ≈−0.01 dB | ≈+0.02 dB |
| 3 kHz | ≈0 dB | ≈0 dB |
| 4 kHz | −6.0 dB | −6.0 dB |
| 5 kHz | −69.9 dB | −75.9 dB |
| 7 kHz | −75.5 dB | −83.2 dB |

Fase es lineal con pendiente correspondiente a 255 muestras, salvo saltos π donde cambia el signo de la respuesta. La ventana determina transición gradual y ondulación; un FIR pasa-banda atenúa frecuencias fuera de banda, no elimina ruido en banda, reverberación ni eco.

Canales aceptados por el módulo: mono/estéreo intercalado, cada canal con su historial independiente. La captura actual es mono. Mantiene la longitud byte a byte y continuidad entre bloques; satura PCM a `[-32768,32767]`. `reset()` borra estado al empezar cada turno para no arrastrar audio previo. El bypass devuelve el mismo bloque sin modificación.

Desactivado por defecto; variables:

```dotenv
CUTY_SPEECH_FIR_ENABLED=0
CUTY_SPEECH_FIR_LOW_HZ=150
CUTY_SPEECH_FIR_HIGH_HZ=4000
```

Se puede hacer A/B en Raspberry al reiniciar el proceso con `CUTY_SPEECH_FIR_ENABLED=0` y `=1`; conservar la misma frase/posición/ganancia y evaluar transcripción y escucha, registrando errores. El inicio valida banda vs Nyquist incluso cuando se desactiva, e informa tasa/taps/retardo. No activar en uso hasta verificar CPU, latencia y reconocimiento en esa Pi. Un cambio de tasa exige construir una instancia nueva para rediseñar coeficientes.

## Pruebas reproducibles

Raspberry: `cd raspberry; .venv/bin/python -m pytest tests/test_speech_bandpass.py tests/test_conversation.py` (en Windows: `.venv\Scripts\python.exe -m pytest ...`). Las pruebas revisan simetría, ganancia, atenuación, retardo, impulso, escalón, mezcla de tonos en banda/fuera de banda, clipping/formato, canales, continuidad de dos particiones equivalentes, bypass y validación de Nyquist. El test de integración usa proveedor falso y comprueba que el bloque filtrado, de la misma longitud, llega a `send_audio`; no conecta a Gemini ni a hardware.

STM32 host: las pruebas C compilan protocolo/estados/trayectoria y FIR mediante `stm32/tests/run_host_tests.py` cuando hay un compilador C de host. El build ARM del proyecto `stm32/blackpill_uart` enlaza FreeRTOS, HAL F401 y callbacks PWM de TIM4; `--profile` habilita salida únicamente con un perfil que confirmó mecánica/mapeo. El build normal conserva PWM bloqueado. `vTaskDelay` no genera PWM; los pulsos se generan con TIM4. La compilación no verifica el comportamiento físico.

La latencia del loop físico de seguimiento, el resultado del reconocimiento con el FIR de voz, el ruido real del cuarto y la respuesta mecánica quedan pendientes de medición en el robot. No reportar la demo sintética del sitio ni la consigna STM32 como medición física.

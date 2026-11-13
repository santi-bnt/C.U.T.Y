# Seguimiento facial de cabeza — estado y calibración

## Alcance actual

El seguimiento de rostros ya existente (`raspberry/src/cuty/vision/face_tracker.py`)
abre la cámara una sola vez y obtiene detecciones localmente con YuNet o Haar.
El controlador nuevo consume ese mismo `FaceTarget`; no inicia otra cámara,
no transmite ni guarda imágenes y no toca audio, expresiones, pantalla, GPIO,
overlays ni firmware.

El CAD V17 coloca la referencia y el soporte de cámara dentro del conjunto
`head`, y define un servo `servo_head` en la base de cabeza, descrito en el CAD
como PAN. Esto confirma la intención del diseño, no el montaje físico actual.
El código STM32 de UART/servos sigue siendo plantilla TODO, sin framing,
asignación de PWM, límites ni calibración. Por ello no hay adaptador de hardware
y el modo físico se rechaza. No se afirma seguimiento físico funcional.

Solo se calcula PID PAN en **unidades normalizadas simuladas**, no grados,
grados/s ni PWM. El error vertical se calcula y se muestra como diagnóstico;
no se acciona porque no hay un eje TILT confirmado. El sentido positivo PAN es
una convención del simulador, no una dirección del servo físico.

## Prueba dry-run en la Raspberry

Por defecto `CUTY_FOLLOW_ENABLED=0`; no cambia el comportamiento de la cara.
Para habilitar la simulación sin cambiar archivos de hardware, crea un override
local de systemd:

```sh
sudo systemctl edit cuty-launcher.service
```

Añade:

```ini
[Service]
Environment=CUTY_FOLLOW_ENABLED=1
Environment=CUTY_FOLLOW_DRY_RUN=1
```

Guarda y reinicia el launcher. El registro muestra `[HEAD FOLLOW DRY-RUN]`,
errores normalizados X/Y, salida PID PAN y velocidad/posición simuladas:

```sh
sudo systemctl daemon-reload
sudo systemctl restart cuty-launcher.service
journalctl -u cuty-launcher.service -f
```

El seguimiento del rostro y la cara animada continúan en el hilo actual.
La posición simulada se mantiene al perder el rostro; a los 0.5 s se pone la
velocidad simulada en cero. La parada interna prevalece sobre las detecciones.
Al apagar el launcher no queda un proceso ni salida física.

Para probar en desarrollo sin cámara ni Raspberry:

```sh
cd raspberry
python -m pytest tests/test_head_follow.py tests/test_face_tracker.py
```

Las pruebas construyen detecciones falsas y un actuador en memoria; no prueban
la cámara real, el altavoz ni el movimiento del robot.

## Parámetros

Todos se leen del entorno al crear `FaceTracker`:

| Variable | Valor inicial | Significado |
| --- | ---: | --- |
| `CUTY_FOLLOW_ENABLED` | `0` | Seguimiento de cabeza habilitado (solo simulación) |
| `CUTY_FOLLOW_DRY_RUN` | `1` | Obligatorio para habilitar; `0` con seguimiento activo se bloquea |
| `CUTY_FOLLOW_KP` | `1.2` | Ganancia proporcional PAN |
| `CUTY_FOLLOW_KI` | `0` | Ganancia integral; comienza desactivada |
| `CUTY_FOLLOW_KD` | `0.08` | Ganancia derivativa PAN |
| `CUTY_FOLLOW_DETECTION_ALPHA` | `0.35` | Suavizado exponencial de la detección, (0, 1] |
| `CUTY_FOLLOW_DERIVATIVE_ALPHA` | `0.25` | Suavizado exponencial de la derivada, (0, 1] |
| `CUTY_FOLLOW_DEADBAND` | `0.035` | Zona muerta del error normalizado |
| `CUTY_FOLLOW_LOST_TIMEOUT` | `0.5` s | Tiempo sin detección antes de detener salida |
| `CUTY_FOLLOW_MAX_DT` | `0.25` s | Tope de dt usado para limitar saltos por pausas |
| `CUTY_FOLLOW_SIM_MAX_VELOCITY` | `0.8` | Límite de velocidad en unidades simuladas/s |
| `CUTY_FOLLOW_SIM_MAX_ACCELERATION` | `1.5` | Límite de aceleración en unidades simuladas/s² |
| `CUTY_FOLLOW_SIM_MIN_POSITION` | `-1.0` | Extremo simulado; no representa ángulo físico |
| `CUTY_FOLLOW_SIM_MAX_POSITION` | `1.0` | Extremo simulado; no representa ángulo físico |

La frecuencia de detección proviene de `CUTY_TRACK_FPS` (12 Hz por defecto).
El controlador mide `dt` con reloj monotónico; un `dt` cero/negativo detiene la
salida y reinicia la derivada. El derivativo se filtra y el integrador usa
anti-windup condicional. Las ganancias operan sobre error normalizado y la
salida simulada se expresa en unidades normalizadas/s; no son parámetros
angulares transferibles al servo.

## Calibración futura del mecanismo físico

No habilites actuadores reales con esta versión. Cuando exista firmware y
protocolo revisados, valida en este orden, con el robot sostenido y un límite
de parada manual accesible:

1. Verifica continuidad mecánica entre cámara y cabeza ensamblada; si la cámara
   queda fija al cuerpo, el error de imagen no cierra el lazo de PAN.
2. Identifica el eje, centro mecánico y recorrido permitido consultando el
   servo, montaje y topes reales; no copies los barridos CAD como límites.
3. Con movimiento mínimo, comprueba qué signo del comando lleva el centro de
   imagen hacia el rostro. Si aumenta el error, invierte la dirección antes de
   seguir: eso detecta retroalimentación positiva.
4. Con `Ki=0`, aumenta `Kp` gradualmente hasta respuesta clara sin oscilación;
   reduce `Kp` si sobrepasa o vibra.
5. Aumenta `Kd` poco a poco para amortiguar sobrepaso. Mantén el filtrado si
   suaviza ruido sin retraso excesivo.
6. Solo tras observar error persistente bajo carga, probar un `Ki` pequeño,
   vigilando saturación y viento del integrador.
7. Reemplaza límites normalizados por límites medidos del mecanismo, y verifica
   velocidad, aceleración, pérdida de detección, parada manual y estado de
   fallo dentro del STM32 antes de cualquier uso autónomo.

La activación también necesita confirmar el pinout UART de la placa montada,
framing/baud/validación del protocolo, canales PWM, direcciones, límites
angulares, alimentación de servos y paradas de seguridad. No se deben alterar
las asignaciones actuales de Raspberry Pi, ReSpeaker o pantalla.

## Archivos de referencia

- `raspberry/src/cuty/vision/face_tracker.py` — cámara única y detección existente.
- `raspberry/src/cuty/vision/head_follow.py` — PID y adaptador simulado.
- `raspberry/src/cuty/hardware/README.md` y `stm32/README.md` — interfaz aún pendiente.
- `hardware/cad/carcasa_v17/fuente_cad/v17/head.py`, `build.py`, `refs.py` —
  colocación de cámara y servo PAN prevista por CAD.

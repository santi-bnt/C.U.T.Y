# Validación física final de C.U.T.Y.

Esta guía cubre los 19 pasos de integración. Las primeras ocho fases verifican el sistema sin autorizar trayectorias del robot; las fases 9–19 requieren calibración progresiva y supervisión presencial. No uses 125° ni los antiguos rangos de laboratorio como límites seguros. La referencia de cada eje es su calibración individual. No ejecutes movimiento a distancia.

## Reglas previas

- Conserva accesible el interruptor físico de alimentación de servos. DISARM retira la señal PWM; no corta la corriente de la fuente ni garantiza que un brazo sostenga una carga.
- La fuente de servos debe ser externa/regulada, con GND común. No alimentes servos desde 3V3, la Raspberry ni ST-Link.
- Mantén manos y cables fuera del mecanismo. Durante la calibración inicial descarga o desacopla el brazo del servo. El comando manual empieza solicitando 1500 us.
- Detén la prueba ante atasco, zumbido sostenido, caída de tensión, reinicio, calentamiento anormal o movimiento distinto al solicitado. Corta la alimentación física si hay riesgo mecánico.
- Nunca conectes a la vez otro programa dueño del UART. `/dev/serial0` puede no ser el UART de los pines del header; en la Pi comprueba el dispositivo y usa el que ya respondió en tu montaje (en la configuración actual se usó `/dev/ttyAMA0`).
- Ninguna fase software crea un perfil mecánico confirmado por ti. El JSON con observaciones de `servo_calibration` queda explícitamente sin confirmar.

## 1. Fuente y GND, sin servos energizados

Con la fuente externa y servos apagados, mide con multímetro las salidas de la fuente y verifica polaridad, continuidad de GND común Pi/STM32/fuente y ausencia de cortos entre alimentación y GND. No uses la salida 3V3 del ST-Link como alimentación de la Black Pill o de un servo.

**Aprobado:** la tensión y polaridad coinciden con la fuente/circuito previstos, GND común está presente y no hay corto. Enciende servos solo en las fases indicadas.

## 2. Raspberry y menú táctil

Arranca la Pi y confirma que aparece el menú. Comprueba el servicio:

```sh
sudo systemctl status cuty-launcher.service --no-pager
```

**Aprobado:** menú visible, táctil responde y el servicio permanece `active (running)`. Si falla, revisa `sudo journalctl -u cuty-launcher.service -n 60 --no-pager`.

## 3. Cámara

Abre la cara C.U.T.Y. desde el menú y colócate frente a la cámara. Revisa que los ojos sigan visualmente la cara. Si la cámara no abre, la cara debe seguir animándose; corrige cámara/servicio antes de autorizar cabeza física.

**Aprobado:** imagen/detecciones nuevas y ojos que responden a la posición de la cara; sin cierre ni bloqueo del menú. Esto no prueba el servo PAN.

## 4. Micrófono y ruta de audio

Desde `raspberry/`, con el mismo entorno virtual del robot:

```sh
cd /home/santi/C.U.T.Y/raspberry
source .venv/bin/activate
python -m cuty --list-audio-devices
python -m cuty --test-microphone
```

**Aprobado:** dispositivo esperado aparece y el medidor responde claramente a voz sin saturación persistente. La prueba de dúplex opcional es silenciosa y no certifica que se oiga la bocina; la salida audible se confirma en el paso 5.

## 5. Conversación Gemini Live

Vuelve al menú y toca C.U.T.Y. Di una frase, espera la respuesta hablada y luego di «salir» para regresar. La clave Gemini debe estar ya en el `.env` privado del robot; no la copies al chat ni al repo.

**Aprobado:** la sesión saluda/escucha, registra voz, responde por la bocina y vuelve al menú por voz sin bloquear pantalla o cámara. Si falla, revisa `sudo journalctl -u cuty-launcher.service -n 60 --no-pager`; no imprimas `.env`.

## 6. UART y heartbeat, sin movimiento

Confirma primero que no hay otro cliente conectado. Desde `raspberry/`:

```sh
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 status
```

**Aprobado:** respuesta V2 válida/ACK y estado `DISARMED`; no aparecen `ARM`, `START` ni pulsos. Si tu puerto difiere, reemplaza `/dev/ttyAMA0` por el dispositivo que identificaste.

## 7. Respuesta y estado seguro del STM32

Repite `status` tres veces, dejando un segundo entre comandos. Revisa que la línea UART y la Black Pill no se reinicien y que cada respuesta sea válida:

```sh
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 status
```

**Aprobado:** tres respuestas V2 válidas, estado inicial DISARMED y ningún servo se mueve. La consulta de estado no comprueba PWM bajo carga.

## 8. Identificación de conectores y ejes

Usa las asignaciones fijas de la carrier: HEAD_PAN=PB6/TIM4_CH1/J7, LEFT_ARM=PB7/TIM4_CH2/J8, RIGHT_ARM=PB8/TIM4_CH3/J9. J10/J11 están reservados. Comprueba continuidad/señal con sistema apagado y etiqueta cables/conectores. Si la identidad física de un servo no se puede confirmar sin movimiento, deja ese eje descargado/desacoplado y usa la calibración manual de los siguientes pasos para comprobar un conector por sesión.

**Aprobado:** cada servo y cable queda asociado a un solo eje/conector y la etiqueta coincide con el pinout. No asumas sentido ni centro común.

## 9. Calibración individual HEAD_PAN

Solo tras compilar y flashear el firmware manual de calibración desde la PC:

```powershell
python stm32/blackpill_uart/build.py --calibration
```

Programa `stm32/blackpill_uart/build/calibration/cuty_arms_pwm_blackpill_calibration.elf` por ST-Link, verifica y reinicia. Deja el mecanismo PAN descargado, confirma cables libres y alimenta el servo con su fuente externa. Desde `raspberry/`:

```sh
PYTHONPATH=src python -m cuty.hardware.servo_calibration --port /dev/ttyAMA0 --axis HEAD_PAN --confirm-unloaded --output head-pan-observations.json
```

Usa `+`/`-` para pasos manuales de 10 us; anota min/centro/max observados y sentido, sin golpear topes. `q` desarma. Revisa el cableado de la cámara durante el recorrido.

**Aprobado:** solo PAN responde, pasos de 10 us son repetibles, no fuerza topes ni tira de cables; `q` o fin normal deja PWM apagado. El archivo es observacional y conserva `mechanical_calibration_confirmed=false`.

## 10. Calibración individual LEFT_ARM

Desacopla/descarga el brazo, confirma el mismo primer pulso de 1500 us y ejecuta:

```sh
PYTHONPATH=src python -m cuty.hardware.servo_calibration --port /dev/ttyAMA0 --axis LEFT_ARM --confirm-unloaded --output left-arm-observations.json
```

**Aprobado:** solo LEFT_ARM responde en pasos manuales pequeños, sus límites observados no fuerzan topes y la sesión termina DISARMED/PWM apagado.

## 11. Calibración individual RIGHT_ARM

Desacopla/descarga el brazo y ejecuta:

```sh
PYTHONPATH=src python -m cuty.hardware.servo_calibration --port /dev/ttyAMA0 --axis RIGHT_ARM --confirm-unloaded --output right-arm-observations.json
```

**Aprobado:** solo RIGHT_ARM responde, se registran centro, recorrido realmente seguro y sentido propios, y el cierre apaga PWM. No copies valores del otro brazo.

## 12. Pruebas cortas, un eje cada vez

Tras revisar las tres mediciones, crea un perfil JSON nuevo con `mechanical_calibration_confirmed=true` y `joint_mapping_confirmed=true` únicamente para valores que hayas medido y confirmado. No marques los ejemplos como confirmados. Configura en el `raspberry/.env` privado:

```dotenv
CUTY_ROBOT_MODE=test
CUTY_TEST_AXIS=LEFT_ARM
CUTY_SERVO_CALIBRATION_PROFILE=/ruta/perfil-confirmado.json
CUTY_STM32_PORT=/dev/ttyAMA0
```

Compila el firmware físico con el mismo perfil revisado:

```powershell
python stm32/blackpill_uart/build.py --profile ruta\al\perfil-confirmado.json
```

Programa `build/physical/cuty_arms_pwm_blackpill_physical.elf`, verifica y reinicia; reinicia también el launcher para cargar el `.env`. Usa un solo `CUTY_TEST_AXIS` por sesión. Desde conversación Gemini, solicita un objetivo del eje elegido, por ejemplo «levanta el brazo izquierdo» solo en sesión `LEFT_ARM`; para `HEAD_PAN`, «mira a la derecha». Para cambiar eje, detén la conversación, cambia `CUTY_TEST_AXIS` en `.env` y reinicia. Si no hay perfil validado, este paso no se puede aprobar ni omitir con `test`.

**Aprobado:** se mueve solo el eje de prueba, responde dentro del recorrido confirmado, el estado/objetivo reportado es comandado y `detente` desarma. Sin atasco ni caída de alimentación.

## 13. Movimiento coordinado limitado

Solo con los tres ejes aprobados por separado, cambia en `raspberry/.env` `CUTY_ROBOT_MODE=robot`, quita `CUTY_TEST_AXIS` y reinicia `cuty-launcher.service`. Mantén servo power accesible y pide una vez: «saluda y mira a la derecha».

**Aprobado:** cabeza y ambos brazos avanzan en una misma trayectoria pequeña y regresan a sus centros calibrados, sin interferencias mecánicas, bloqueos o reinicios. Detén ante cualquier contacto o carga inesperada.

## 14. Seguimiento facial físico

Configura el entorno privado de voz y del launcher con `CUTY_ROBOT_MODE=robot`, `CUTY_SERVO_CALIBRATION_PROFILE` apuntando al perfil confirmado, `CUTY_STM32_PORT=/dev/ttyAMA0`, `CUTY_FOLLOW_PHYSICAL_ENABLE=1` y `CUTY_FOLLOW_DRY_RUN=0`. Reinicia `sudo systemctl restart cuty-launcher.service`; comprueba en el log enlace válido/DISARMED. Entra a la cara y mantén la pantalla pulsada entre 0.7 y 5 s para armar. Mueve la cara lentamente a izquierda/derecha y vuelve a perderla por más de 0.5 s.

**Aprobado:** solo HEAD_PAN acompaña de forma progresiva; con detección perdida se detiene/desarma y no vuelve a moverse hasta otro toque. No debe perseguir objetivos antiguos ni tocar topes. Esto no autoriza aumentar ganancias automáticamente.

## 15. Gestos

Con modo `robot`, cabeza/brazos en sus centros y supervisión presencial, solicita de uno en uno «saluda con el brazo izquierdo», «saluda con el brazo derecho» y, solo si ambos brazos pasaron la fase 12, «saluda con ambos brazos».

**Aprobado:** cada gesto usa el perfil y la ruta de movimiento compartida, completa posiciones cortas y termina en centro; sin conflicto con seguimiento. Un gesto no calibrado se rechaza o no se prueba.

## 16. Comandos por voz

Prueba individualmente «mira a la izquierda», «mira a la derecha», «levanta el brazo izquierdo», «levanta el brazo derecho», «regresa al centro» y «detente». Prueba una frase ambigua/inventada y confirma que no produzca movimiento.

**Aprobado:** solo frases explícitas de la allowlist producen objetivos, el comando `detente` gana prioridad y la frase inválida se rechaza. La expresión facial puede cambiar junto con un saludo; no sustituye el ACK/estado del controlador.

## 17. Pérdida y recuperación de UART

Hazlo sin carga peligrosa y con interruptor físico a mano. Con actuadores en reposo y una sesión supervisada, interrumpe solo la comunicación UART, no GND ni alimentación, y espera el watchdog. Reconecta UART y consulta:

```sh
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 status
```

Si el controlador quedó en FAULT, limpia la causa antes de autorizar recuperación; `RESET` debe ser una acción manual explícita. Reinicia la aplicación para revalidar enlace/perfil. No pidas movimiento durante la desconexión.

**Aprobado:** la pérdida causa estado seguro/FAULT y PWM inactivo; reconectar no arma ni reanuda. Tras restablecer, sigue desarmado hasta una acción explícita y válida.

## 18. Parada, desconexión y reinicio

Con una prueba pequeña autorizada, di «detente» y verifica DISARMED. Después prueba detener la aplicación y reiniciar la Pi/STM32, una acción a la vez. Desconectar o detener software no equivale a cortar la fuente del servo; usa el interruptor físico cuando necesites quitar energía.

**Aprobado:** stop detiene la trayectoria actual sin que queden consignas posteriores; al reiniciar no hay movimiento no solicitado y la nueva conexión exige autorización nueva. Si el servo sigue ejerciendo torque sin PWM, corta su fuente físicamente.

## 19. Funcionamiento prolongado

Solo tras aprobar las etapas anteriores, corre la sesión funcional bajo observación por un periodo elegido para la prueba. Comprueba UART, audio, cámara, pantalla, estabilidad de alimentación, corriente de la fuente y temperatura de regulador, Black Pill y servos a intervalos regulares. No bloquees deliberadamente servos para medir corriente.

**Aprobado:** no hay reinicios, ACK perdidos, movimiento espontáneo, zumbido sostenido, conectores/cables calientes, caídas de tensión ni deriva mecánica. Registra duración, corrientes, temperaturas y fallos; no declares validación prolongada sin esas mediciones.

## Compilación, pruebas y programación

Desde la raíz del repositorio, `python stm32/blackpill_uart/build.py` genera firmware normal con salidas PWM bloqueadas; `--calibration` genera calibración manual; `--profile` requiere el JSON confirmado. Usa los artefactos de la carpeta correspondiente y no grabes un ELF de banco como firmware normal. Programa con CubeProgrammer/ST-Link, verifica escritura y reinicia. La conexión SWD es ST-Link SWDIO→PA13, SWCLK→PA14, GND común y NRST opcional.

El software probado y los builds ARM no certifican corriente, recorrido, temperatura, sentido, compatibilidad de conectores ni funcionamiento ensamblado. Los datos observados de calibración no forman un perfil hasta que el usuario confirme físicamente el mapeo y límites.

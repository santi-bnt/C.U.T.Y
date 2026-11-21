# Servos de la Black Pill desde la Raspberry

Version sencilla basada en tu carpeta `cuty_arms_pwm_blackpill` de Documentos:
STM32F401CCU6, HSI de 16 MHz y FreeRTOS, adaptada a TIM4 y a los pines del repo.
Reemplaza el barrido automatico
por comandos UART. El firmware se graba en la Black Pill; en la Pi corre Python.

## Conexiones de esta prueba

| Raspberry Pi | Black Pill | Funcion |
| --- | --- | --- |
| Pin fisico 8, GPIO14 TX | PA3 RX | Comandos |
| Pin fisico 10, GPIO15 RX | PA2 TX | Respuestas |
| Pin fisico 6, GND | GND | Tierra comun |

| Servo en el comando | Articulacion | Conector | Senal | Temporizador |
| --- | --- | --- | --- | --- |
| 1 | HEAD_PAN / cabeza | J7 | PB6 | TIM4 CH1 |
| 2 | LEFT_ARM / brazo izquierdo | J8 | PB7 | TIM4 CH2 |
| 3 | RIGHT_ARM / brazo derecho | J9 | PB8 | TIM4 CH3 |

Esta asignacion sigue la carrier v1.1 documentada en el repo. J10/PB9 y
J11/PA8 quedan reservados, sin PWM. PA1 queda disponible para el divisor de
bateria y PB10 para I2C; esta prueba no configura esos perifericos.
Si tus servos estaban conectados como en el proyecto original, mueve sus
senales a PB6/PB7/PB8 antes de ejecutar esta version.

UART usa 3.3 V. Alimenta los servos con una fuente externa adecuada a su modelo
y corriente, nunca desde 3V3. Une su negativo con GND de las placas. Empieza
con un motor sin carga: 1500 us no garantiza un centro fisico calibrado.

## Compilar y cargar en la Black Pill

Desde la raiz del repo, con Python y STM32CubeIDE instalados:

```powershell
python stm32/blackpill_uart/build.py
```

Genera `build/cuty_arms_pwm_blackpill.elf` y `.bin`. Encuentra GCC de CubeIDE
bajo `C:/ST`; tambien acepta `--cc RUTA/arm-none-eabi-gcc.exe`. En Linux sirve
el mismo script con GCC ARM en PATH.

Con ST-Link: SWDIO a PA13, SWCLK a PA14, GND a GND y referencia/alimentacion
de 3.3 V segun tu programador. En STM32CubeProgrammer selecciona ST-LINK,
conecta, programa el `.elf`, verifica y reinicia. Para `.bin` usa la direccion
`0x08000000`. El cable UART con la Pi transmite comandos; no graba por si solo
este firmware. No se ha grabado ninguna placa desde esta sesion.

Tambien puedes importar esta carpeta como proyecto existente en CubeIDE y
compilar `cuty_arms_pwm_blackpill`. Evita importar el proyecto original con el
mismo nombre al mismo workspace. No hace falta regenerar el `.ioc`; si lo
haces, revisa los cambios de inicializacion antes de grabar.

## UART de la Raspberry Pi 5

En `sudo raspi-config`, desactiva la consola de inicio de sesion por serie.
En `/boot/firmware/config.txt`, bajo una seccion aplicable como `[all]`, agrega
`dtoverlay=uart0-pi5` si no existe y reinicia. Habilita UART0 en GPIO14/15.
Comprueba con `pinctrl get 14 15` y `ls -l /dev/ttyAMA*`.

En Pi 5 `/dev/serial0` puede corresponder al conector de depuracion. Los ejemplos
usan `/dev/ttyAMA0`: confirma que sea UART0 de GPIO14/15 en tu sistema. Para
permisos: `sudo usermod -aG dialout "$USER"` y vuelve a iniciar sesion.
Deja el puerto libre de otros programas y de la consola serie.

Referencias: [UART en Raspberry Pi](https://www.raspberrypi.com/documentation/computers/configuration.html#configure-uarts)
y [overlay oficial uart0-pi5](https://github.com/raspberrypi/firmware/blob/master/boot/overlays/README).

## Ejecutar en la Raspberry

Con una copia de este repo en la Pi, desde su raiz:

```bash
python3 -m venv .venv-servos
.venv-servos/bin/python -m pip install 'pyserial>=3.5,<4'

# Primero comprobar UART: mantiene TODOS los PWM apagados.
.venv-servos/bin/python raspberry/scripts/servos_uart.py --port /dev/ttyAMA0

# Activar solo el servo 1 durante tres segundos.
.venv-servos/bin/python raspberry/scripts/servos_uart.py --port /dev/ttyAMA0 --servo 1 --us 1500 --seconds 3
```

Cambia `--servo` a 2 o 3 para los otros canales. El script comienza y termina
con STOP para los tres canales y envia PING cada 0.5 segundos. Ctrl+C intenta
enviar STOP. No ejecutes varias copias a la vez. Si ya usas el entorno del
proyecto, puedes instalar el extra `servos` de `raspberry/pyproject.toml`.

## Comandos y limites

**115200 baudios, 8N1**, sin control de flujo. Cada linea termina en LF; tambien
acepta CRLF. Envia un comando y espera su respuesta antes del siguiente.

| Comando | Respuesta | Efecto |
| --- | --- | --- |
| `STOP` | `OK STOP` | Apaga los tres PWM y libera el bloqueo por error |
| `PING` | `OK PING` | Mantiene comunicacion; no activa salidas |
| `SERVO,1,1500` | `OK SERVO` | Activa/actualiza servo 1 con pulso de 1500 us |

Acepta servos 1–3 y **1000–2000 us**, a 50 Hz; no son grados. Se excluyeron los
extremos originales de 2700/2850 us para esta primera prueba. Calibra antes de
ampliar el rango. Cambia directamente de posicion, sin rampa, FIR ni PID.
Otros canales conservan su orden hasta STOP o timeout; el script solo activa
uno por ejecucion.

Al arrancar no hay PWM. Dos segundos sin comando valido, entradas incorrectas,
una linea incompleta durante 250 ms o un fallo de recepcion apagan las salidas.
Se exige STOP antes de otro movimiento: PING no desbloquea. Errores posibles:
`ERR COMMAND`, `ERR LINE`, `ERR STOP_REQUIRED`, `ERR PWM`. El timeout no envia
respuesta espontanea. Apagar PWM retira la senal: no corta alimentacion ni
garantiza que una carga mantenga su posicion.

Esta prueba no ejecuta el protocolo V2 ni `stm32/App`, ni conecta voz,
seguimiento de cabeza o dashboard. No tiene realimentacion de posicion ni
watchdog independiente. La integracion completa sigue pendiente.

## Codigo y pruebas

`Core/Src/servo_uart.c` contiene el control comentado y `servo_command.c` valida
comandos. `main.c` inicializa el hardware. `../../raspberry/scripts/servos_uart.py`
es el cliente comentado. Drivers/CMSIS y FreeRTOS proceden de tu proyecto;
se completo UART HAL desde el paquete local STM32CubeF4 V1.28.3.

```bash
python stm32/blackpill_uart/tests/run_tests.py --cc gcc
python -m unittest discover -s raspberry/tests -p test_servos_uart.py
```

Se comprobaron compilacion/enlace ARM y logica con UART/PWM simulados.
La carga, la comunicacion fisica y la calibracion siguen pendientes en tu equipo.

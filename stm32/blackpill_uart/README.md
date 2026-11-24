# CubeIDE STM32F401: UART V2 con PWM bloqueado

Existe un [build separado de calibración manual](../../docs/servo-calibration.md).
Genera con `python stm32/blackpill_uart/build.py --calibration` desde la raíz.
Solo ese build permite `V2,CAL` en READY para un servo; START/TARGET no mueven
los motores. Las indicaciones de PWM bloqueado de esta página describen el build
normal, sin esa opción.

Este proyecto parte del proyecto STM32CubeIDE de la Black Pill STM32F401CCU6 y
compila la aplicación portable de C.U.T.Y. en `../App` junto con HAL de USART2/TIM4,
FreeRTOS y CMSIS-RTOS2 incluidos en el proyecto. No usa la antigua prueba
`PING/STOP/SERVO`: esa interfaz no era compatible con el puente V2 de Raspberry.

## Build

### Prueba física de un servo suelto por V2

Para probar movimiento sin declarar calibrado el robot, el build optativo
`python stm32/blackpill_uart/build.py --bench-channel 1` habilita solo PB6/J7.
`2` selecciona PB7/J8 y `3`, PB8/J9. El ELF/BIN queda separado en
`build/bench-j7/` (o `bench-j8/`, `bench-j9/`); hay que cargar ese firmware.
El build normal y el de CubeIDE mantienen las salidas físicas bloqueadas.

Conecta un solo servo suelto, sin el mecanismo: señal al pin seleccionado,
alimentación regulada para el servo y GND común. No alimentes el servo desde
3V3 ni desde ST-Link. La alimentación de servos de la carrier está diseñada
para 6 V. La prueba no valida la alimentación ni los límites mecánicos.

En Raspberry, desde `raspberry/`, con `pyserial` instalado:

```bash
PYTHONPATH=src python -m cuty.hardware.servo_bench --port /dev/ttyAMA0 --channel 1 --target 1000 --seconds 3
PYTHONPATH=src python -m cuty.hardware.servo_bench --port /dev/ttyAMA0 --channel 1 --target -1000 --seconds 3
```

El canal del comando debe coincidir con el build. Los índices son eléctricos,
no confirman a qué articulación corresponde el servo conectado. `START` aplica
1500 us; la consigna pasa por el controlador de trayectoria hasta 1600 o 1400 us,
respectivamente. Esta ventana reducida tampoco es segura por definición para
un mecanismo montado. No se usan aquí los extremos experimentales de 2700/2850 us.
No hay barrido al encender. El script mantiene HB en una única sesión y desarma
al terminar, ante NACK, error o Ctrl+C. El timeout de heartbeat de 500 ms quita
PWM si se pierde el enlace; quitar PWM no corta alimentación ni garantiza torque
cero. No uses el antiguo `servos_uart.py`, que habla otro protocolo.

### Compilación normal sin movimiento

Abre esta carpeta en STM32CubeIDE y compila `Debug`, o desde la raíz del repositorio
ejecuta:

```powershell
python stm32/blackpill_uart/build.py
```

El script usa `arm-none-eabi-gcc` del PATH o busca STM32CubeIDE en `C:/ST`. Para
otra instalación, indica `--cc ruta\arm-none-eabi-gcc.exe`. Si falta el compilador,
el comando informa el requisito y no descarga herramientas. Un build exitoso genera
`build/cuty_arms_pwm_blackpill.elf`, `.bin` y `firmware.map`.

## Arranque y seguridad

El MCU usa HSI de 16 MHz. TIM4 se configura desde el HAL para contar a 1 MHz y periodo
de 20 ms: PB6/TIM4_CH1→J7, PB7/TIM4_CH2→J8 y PB8/TIM4_CH3→J9. Los tres GPIO se
configuran bajos y todos los CCR quedan en cero; ningún canal arranca. El firmware no
enlaza los callbacks físicos de salida con FreeRTOS. Por eso `V2,START` puede aceptar
el estado lógico ACTIVE, pero no activa PWM. No existe barrido al encender. J10/PB9 y
J11/PA8 siguen reservados.

El UART USART2 es 115200, 8N1, sin control de flujo y lógica de 3.3 V. La ISR recibe
un byte y lo deposita en una cola; el parser, los cambios de estado y las respuestas
se procesan en tareas. Una tarea TX única emite ACK/NACK, cambios de estado y
telemetría. La pérdida de UART/heartbeat lleva al controlador a FAULT; `RESET`
recupera explícitamente el estado lógico y `DISARM` no borra un FAULT.

Las muestras experimentales permanecen en `../Board/servo_calibration.h`: servo de
prueba 1 = 1000–2850 µs, 2 = 1000–2700 µs, 3 = 1000–2850 µs, a 50 Hz. No se conoce su
correspondencia con ejes, centro, dirección ni límites mecánicos seguros. No cambies
las confirmaciones de calibración/mapeo ni la compuerta de build sin validar el
mecanismo y la protección eléctrica.

## Flashear con ST-Link

Con el build terminado, conecta ST-Link SWDIO→PA13, SWCLK→PA14, GND→GND y NRST si está
disponible. Usa alimentación regulada para la Black Pill y asegúrate de que ST-Link
detecte el voltaje de referencia objetivo. En STM32CubeProgrammer selecciona
ST-LINK/SWD, conecta, programa el ELF (o el BIN en `0x08000000`), verifica y reinicia.
No conectes los servos para comprobar la UART. La compilación y las pruebas host no
demuestran que una Black Pill concreta haya arrancado.

## Cableado y prueba UART

| Raspberry Pi 5 | STM32F401 / carrier | Señal |
| --- | --- | --- |
| GPIO14, pin físico 8 TX | PA3 / USART2_RX | Pi→STM32 |
| GPIO15, pin físico 10 RX | PA2 / USART2_TX | STM32→Pi |
| GND, pin físico 6 | GND | Referencia común |

Verifica con multímetro que las señales sean 3.3 V. En la Raspberry instala el
paquete si hace falta (`python -m pip install pyserial`), libera la consola serial,
habilita UART0 en GPIO14/15 y añade tu usuario a `dialout`. Identifica el dispositivo
real con `ls -l /dev/ttyAMA* /dev/serial*`; no supongas que `/dev/serial0` apunta a
los pines del header.

Desde `raspberry/` con el entorno virtual activo:

```bash
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 status
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 send V2,ARM
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 send V2,START
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 target HEAD_PAN 350
PYTHONPATH=src python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 send V2,DISARM
```

`status` envía un heartbeat y presenta el ACK, sin armar ni iniciar. Los objetivos
solo cambian consignas software y requieren ACTIVE; no producen movimiento en esta
compilación. El puente desarma al cerrar y toma un lock exclusivo del puerto. Si la
prueba informa una respuesta inválida, captura la línea UART cruda y el estado del
build/flasheo; no sustituyas el protocolo por `PING`.

## Pruebas de software

```bash
python stm32/tests/run_host_tests.py
python -m unittest discover -s raspberry/tests
```

Estas pruebas verifican lógica y dobles de host. La validación física de RX/TX requiere
Black Pill, cableado y una respuesta recibida en la Pi; no se declara realizada aquí.

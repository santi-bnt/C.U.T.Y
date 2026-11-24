# Calibración manual de los MG996R

Esta prueba mueve **un solo servo** desde la Raspberry. No inicia seguimiento de
cámara ni movimientos automáticos. Conserva UART V2, el watchdog corregido y los
pines del repo: HEAD_PAN en PB6/J7, LEFT_ARM en PB7/J8 y RIGHT_ARM en PB8/J9.

## Antes de activar

El primer pulso será **1500 us**: es una referencia eléctrica y puede producir un
salto si el eje está en otra posición. Descarga el mecanismo o desacopla el brazo
del servo para esa primera prueba, sostén cualquier pieza que pueda caer y deja
libres los cables de la cámara. No se conoce todavía el centro mecánico real.
La opción `--confirm-unloaded` confirma esa preparación; el programa no la detecta.

Alimenta los servos con los 5 V previstos, mediante su fuente externa y con GND
común con ambas placas. Durante esta prueba no deben alimentarse desde 3V3 ni
circular sus corrientes por las placas de control. Si la tensión cae, hay reinicios
o un motor se atasca, detén la prueba y revisa la alimentación/mecánica.

## Firmware específico

Desde la raíz del repo, en la computadora de programación:

```powershell
python stm32/blackpill_uart/build.py --calibration
```

Genera archivos separados:

```text
stm32/blackpill_uart/build/calibration/cuty_arms_pwm_blackpill_calibration.elf
stm32/blackpill_uart/build/calibration/cuty_arms_pwm_blackpill_calibration.bin
```

Graba el ELF con STM32CubeProgrammer y ST-Link V2, verifica, desconecta la sesión
de programación y reinicia. Para BIN, la dirección es `0x08000000`. Al arrancar
todos los canales permanecen apagados. No hace falta cambiar el `main.c` ni el
`.ioc` para este build. `Build Debug` de CubeIDE sin el símbolo adicional y el
script **sin** `--calibration` mantienen bloqueados los motores.

## Sesión desde la Raspberry

Actualiza la copia de este código en la Pi. Desde `raspberry/`, con el entorno
virtual activo y `pyserial` instalado, empieza por el brazo izquierdo:

```bash
PYTHONPATH=src python -m cuty.hardware.servo_calibration --port /dev/ttyAMA0 --axis LEFT_ARM --confirm-unloaded
```

El programa envía DISARM, HB, ARM y CAL. No envía START. Si encuentra FAULT, se
detiene: revisa la causa y repite agregando `--reset-fault` únicamente para
autorizar el RESET. No reconecta ni rearma automáticamente tras un fallo.

Escribe una de estas opciones y pulsa Enter:

| Entrada | Acción |
| --- | --- |
| `+` | Aumenta 10 us el pulso solicitado |
| `-` | Reduce 10 us el pulso solicitado |
| `min` | Anota la posición como mínimo observado |
| `centro` | Anota la posición central observada |
| `max` | Anota la posición como máximo observado |
| `invertir` | Alterna la anotación del sentido; no mueve ni invierte el motor |
| `q` | Apaga PWM, guarda las anotaciones y sale |

El heartbeat continúa aunque no escribas nada. La sesión dura 45 segundos por
defecto; `--seconds` acepta de 1 a 55. Para repetir mediciones, usa otro archivo:

```bash
PYTHONPATH=src python -m cuty.hardware.servo_calibration --port /dev/ttyAMA0 --axis LEFT_ARM --confirm-unloaded --output brazo-izquierdo-prueba2.json
```

Después de ese brazo, repite con RIGHT_ARM; por último HEAD_PAN, considerando
la carga y los cables de la cámara. Cambiar de eje requiere cerrar/desarmar y
abrir otra sesión. Detener PWM retira la señal, pero no corta la alimentación
ni garantiza que el mecanismo sostenga una carga.

## Qué se limita y qué falta medir

- `V2,CAL,LEFT_ARM,1500` solicita un pulso en microsegundos, no un ángulo.
- Solo el build de calibración enlaza el driver manual; el build normal lo rechaza.
- Exige READY después de ARM y heartbeat vigente, con caducidad de 500 ms.
- La primera orden de cada sesión debe ser 1500 us; después admite cambios de
  hasta 10 us separados al menos 100 ms, dentro de **1000–2000 us**.
- Esa ventana es un límite de software, **no un recorrido mecánico seguro
  confirmado**. No busques el extremo haciendo que el motor golpee o se atasque.
- El firmware apaga el canal ante DISARM, error UART/trama, rechazo de órdenes,
  heartbeat vencido o un máximo de 60 segundos por sesión, aunque sigan los HB.
- START/TARGET durante la calibración se rechazan y apagan la salida. No se
  modifican las confirmaciones de `stm32/Board/servo_calibration.h`.

El JSON guarda `observed_points`, el eje, el pin y la anotación de sentido.
`mechanical_calibration_confirmed` queda en **false**. Son pulsos solicitados,
no posiciones medidas; una anotación con solo un punto tampoco es una calibración
completa. No se sobrescriben archivos existentes y no se escribe en la Flash de
la Black Pill. `q` o el fin normal de la sesión guardan los datos; Ctrl+C o un
error solicitan apagado, pero no guardan anotaciones incompletas.

El paso posterior será revisar esos datos, verificar `min < centro < max`,
asignación y sentido, y configurar por articulación el movimiento automático.
Esta herramienta no hace esa habilitación por sí sola.

## Verificación realizada

Se prueban el parser y los límites, la tarea RTOS con UART simulado y el driver
HAL con GPIO/timers simulados, incluyendo pérdida de heartbeat y errores. También
se compilan ambos firmwares ARM y se prueba el cliente de la Pi. Estas pruebas
no validan el movimiento real de tus servos: falta cargar el nuevo firmware y
realizar las mediciones en el equipo.

# Firmware STM32 de C.U.T.Y.

Para la primera prueba de movimiento, usa el [modo de calibración manual](../docs/servo-calibration.md):
`python stm32/blackpill_uart/build.py --calibration` genera un ELF separado que
acepta `V2,CAL` para un único eje. La descripción de PWM bloqueado que sigue
corresponde al build normal; la calibración no habilita el control automático.

El proyecto reproducible para la Black Pill STM32F401CCU6 está en
[`blackpill_uart/`](blackpill_uart/README.md). Integra los módulos portables de
[`App/`](App/) y la capa HAL de [`Board/`](Board/) con el proyecto STM32CubeIDE,
USART2 y CMSIS-RTOS2/FreeRTOS. La Raspberry usa GPIO14/pin 8 TX → PA3 USART2_RX;
PA2 USART2_TX → GPIO15/pin 10 RX. UART: 115200, 8N1, sin control de flujo, lógica
3.3 V y GND común.

El firmware del CubeIDE es el responsable de la respuesta V2, los estados y la
telemetría. USART2 recibe por interrupción y la ISR solo entrega bytes a la cola
FreeRTOS; las tareas procesan el protocolo y una única tarea transmite respuestas.
El parser acepta `V2,HB`, `ARM`, `START`, `DISARM`, `RESET` y objetivos V2 para
HEAD_PAN, LEFT_ARM y RIGHT_ARM. Las respuestas son `V2,ACK,...`, `V2,NACK,...`,
`V2,STATE,...` y `V2,TELEM,...`.

TIM4 está inicializado para PB6/PB7/PB8 → J7/J8/J9, pero los pines arrancan como
GPIO bajos y ningún canal PWM se inicia. `START` solo cambia el estado lógico en
esta compilación: no se enlaza una ruta de salida física y no hay barrido de inicio.
Las mediciones provisionales 1000–2850, 1000–2700 y 1000–2850 µs siguen asociadas
por número de servo de prueba, no por articulación. Centro, sentido, asignación y
límites mecánicos seguros requieren validación individual. J10/J11 permanecen
reservados.

Desde `stm32/blackpill_uart`, compilar con `python build.py` genera ELF, BIN y MAP
si `arm-none-eabi-gcc` está en PATH o en la instalación local de STM32CubeIDE.
También se puede importar la carpeta en STM32CubeIDE y compilar Debug. La
programación por ST-Link usa SWDIO, SWCLK, GND y opcionalmente NRST; verifica antes
la alimentación y el voltaje objetivo. La compilación host no valida el hardware.

Para pruebas host del controlador y las tareas:

```sh
python stm32/tests/run_host_tests.py
```

Consulta [arquitectura FreeRTOS](../docs/freertos-motion-control.md),
[protocolo](../docs/protocol/protocol.md), [cableado](../docs/wiring.md) y la guía
del [puente UART de Raspberry](../raspberry/src/cuty/hardware/README.md).

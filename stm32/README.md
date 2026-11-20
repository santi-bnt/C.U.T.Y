# C.U.T.Y STM32F401 Firmware

Stage 1 targets Raspberry Pi 5 UART diagnostics on the carrier v1.1 with actuator outputs held safe. J10/J11 are reserved. Board-level HAL application code exists, but this repository does not yet contain the generated CubeIDE project or the STM32F4 HAL/FreeRTOS package needed for a complete link. No flashable firmware is claimed.

The carrier BOM, schematic and netlist specify a **WeAct Black Pill STM32F401CCU6**. Confirm the actual fitted module marking/revision before programming. This part is Cortex-M4, 256 KiB Flash and 64 KiB SRAM; use the exact STM32F401CC device support package and verify the datasheet/package. Carrier UART is Pi GPIO14 physical pin 8 TX → PA3 USART2_RX and PA2 USART2_TX → Pi GPIO15 physical pin 10 RX, common GND, 3.3 V logic.

`Core/` and `Drivers/` are reserved for STM32CubeMX startup and CMSIS/HAL. They remain empty. Install STM32CubeIDE (bundled GNU Tools for STM32) and STM32CubeMX with STM32CubeF4 package support, generate the STM32F401CCU6 project and CMSIS-RTOS2/FreeRTOS integration before a hardware build can be made. Do not copy files from another MCU family. USART2 is 115200, 8 data bits, no parity, 1 stop bit, no flow control. The display/ReSpeaker pin mappings are untouched.

## Archivos oficiales que faltan para el build completo

La búsqueda local encontró un proyecto CubeIDE `EJEMPLO`, pero es para NUCLEO-H745ZI-Q / STM32H745ZI dual-core. No se usa para compilar el F401. También se encontró CubeIDE 2.2.0 y su compilador GNU Tools for STM32 14.3.1; el repositorio STM32Cube local contiene solo STM32Cube_FW_H7_V1.13.0, no STM32Cube_FW_F4.

Para generar el proyecto correcto, instala en CubeIDE el paquete **STM32Cube FW_F4 V1.28.0**, que es la versión declarada por `CUTY_F401.ioc`. Abre ese `.ioc`, confirma STM32F401CCU6, habilita FreeRTOS con interfaz CMSIS-RTOS v2 y genera el proyecto CubeIDE. El `.ioc` actual documenta reloj, USART2 y arranque bajo de PB6–PB8; todavía no contiene la configuración FreeRTOS generada.

El proyecto generado debe aportar, sin crear sustitutos manuales:

- `.project`, `.cproject`, la configuración `.settings/` y el `.ioc` revisado.
- `Core/Inc/stm32f4xx_hal_conf.h`, `Core/Inc/FreeRTOSConfig.h`, `Core/Inc/main.h` e `Core/Inc/stm32f4xx_it.h`.
- `Core/Src/stm32f4xx_hal_msp.c`, `Core/Src/stm32f4xx_it.c`, `Core/Src/system_stm32f4xx.c` y los archivos de soporte C generados que referencie el proyecto.
- El startup assembly y linker script FLASH que CubeIDE genere para el dispositivo STM32F401CCUx.
- Las carpetas oficiales `Drivers/CMSIS/` y `Drivers/STM32F4xx_HAL_Driver/` del paquete F4.
- El FreeRTOS oficial del paquete seleccionado: kernel, `portable/GCC/ARM_CM4F`, `portable/MemMang/heap_4.c` y `Source/CMSIS_RTOS_V2/cmsis_os2.c`, según los archivos que registre el proyecto generado.

Integra los módulos `App/` y `Board/` de este repositorio en ese proyecto. Usa `Board/main.c` como único `main()`; no compiles simultáneamente otro `main.c` generado. En `stm32f4xx_it.c`, el único `USART2_IRQHandler` debe llamar `cuty_board_usart2_irq_handler()`. Conserva el `SysTick_Handler` generado para FreeRTOS: debe avanzar el tick de HAL y delegar al handler del port FreeRTOS. Configura USART2_IRQn en prioridad 6 y `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY` en 5 (con cuatro bits de prioridad NVIC), ya que la recepción llama a APIs CMSIS-RTOS desde la ISR. Mantén `configTICK_RATE_HZ=1000`; `cuty_rtos_create()` rechaza otra frecuencia.

`App/` contains portable C parsing, the HEAD_PAN five-tap FIR and trajectory, limits, heartbeat/state logic, pulse conversion and CMSIS-RTOS2 tasks. `Board/` provides USART2 on PA3/PA2 and a TIM4 PWM driver for PB6/PB7/PB8 (J7/J8/J9). The PWM channels are configured with compare zero, GPIOs stay low, and no channel is started at boot. Physical output is compile-time disabled and also requires explicit arm, fresh heartbeat, safety readiness, confirmed mechanical calibration and confirmed servo-to-joint mapping. A single-channel manual pulse API is prepared for later bench tests; it has the same gates and does not sweep. `CUTY_FREEZE_COMMAND` only holds a logical setpoint; it is not a safe physical fault policy because an energized servo may stall or overheat. The measured provisional ranges are stored by test number in `Board/servo_calibration.h`; they are not yet associated with axes and cannot enable movement. `V2,START` therefore cannot control actuators in this build. See [FreeRTOS architecture, status and tests](../docs/freertos-motion-control.md).

The three independent bench results were 1000–2850 µs, 1000–2700 µs and 1000–2850 µs at 50 Hz; about 150° total travel was observed. This does not establish a 180° servo range, a 75° center, a direction, or safe mechanical endpoints. The code treats each tested interval as an upper software boundary pending new tests. Do not enable output until each assembled mechanism has confirmed minimum, center, maximum, direction, velocity/acceleration limits and connector mapping. No startup sweep is present.

Read [body control](../docs/body-control.md), [wiring](../docs/wiring.md), and [shared protocol](../docs/protocol/protocol.md). The HAL USART2 interrupt RX, task-owned TX, and V2 response code are in `Board/cuty_board.c`; generated `stm32f4xx_it.c` must delegate its single `USART2_IRQHandler` to `cuty_board_usart2_irq_handler()` to avoid duplicate vector definitions. Use the board `main.c` in place of CubeMX's generated main so startup creates the existing application tasks and does not create a second scheduler setup. To program after the F401 CubeIDE project is generated and linked: build Debug, then use ST-LINK SWD (SWDIO, SWCLK, GND, optionally NRST; target powered and voltage sensed) with STM32CubeProgrammer or CubeIDE Run/Debug. A host test or object-only ARM compile does not verify a Black Pill.

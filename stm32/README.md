# C.U.T.Y STM32F401 Firmware

Owns real-time physical control: PWM, servo motion, head PAN, left arm and right arm, future IMU acquisition, and safety limits. J10 and J11 are reserved; physical control remains unvalidated.

The current control hardware is an **STM32F401 Black Pill**, also targeted by the [carrier PCB v1.1](../hardware/electronics/kicad/cuty_carrier/README.md). Confirm the exact MCU suffix and board revision before generating firmware.

For a simple UART/servo bench test, use [blackpill_uart](blackpill_uart/README.md). It imports the supplied STM32F401CCU6 CubeIDE project, adds USART2 on PA2/PA3 and controls TIM4 PWM on PB6/PB7/PB8 (J7/J8/J9). It includes a build script and a Raspberry client. These servo pins follow the carrier PCB assignment: HEAD_PAN, LEFT_ARM and RIGHT_ARM. J10/J11 remain reserved. Physical validation remains pending.

The top-level `Core/` and `Drivers/` remain reserved for future integration of the portable application with the carrier pinout.

`App/` includes portable C parsing, the HEAD_PAN five-tap FIR and trajectory, limits, heartbeat/state logic and pulse conversion, plus an initial dry-run CMSIS-RTOS2 adapter in `App/rtos/`. It is not linked into the independent bench firmware; its physical integration remains pending. IMU is an interface only and PID remains a placeholder. See [FIR DSP](../docs/digital-signal-processing-fir.md) and [FreeRTOS architecture, status and tests](../docs/freertos-motion-control.md).

Read [body control](../docs/body-control.md), [wiring](../docs/wiring.md), and [shared protocol](../docs/protocol/protocol.md). Follow the separate bench guide for flashing; the portable application remains a dry-run skeleton.

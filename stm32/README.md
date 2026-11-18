# C.U.T.Y STM32F401 Firmware

Owns real-time physical control: PWM, servo motion, head PAN, left arm and right arm, future IMU acquisition, and safety limits. J10 and J11 are reserved; physical control remains unvalidated.

The current control hardware is an **STM32F401 Black Pill**, also targeted by the [carrier PCB v1.1](../hardware/electronics/kicad/cuty_carrier/README.md). Confirm the exact MCU suffix and board revision before generating firmware.

`Core/` and `Drivers/` are reserved for the STM32F401 board-specific CubeMX/startup and CMSIS/HAL project. No generated HAL, clock configuration or firmware build system is supplied yet. The carrier's UART/PWM/ADC pin assignments document the PCB design; firmware initialization and physical validation remain pending.

`App/` now includes portable C parsing, commanded-position filtering, limits, heartbeat/state logic and pulse conversion, plus an initial dry-run CMSIS-RTOS2 adapter in `App/rtos/`. IMU is an interface only and PID remains a placeholder. No board UART/PWM drivers or flashable STM32 image exist. See [FreeRTOS architecture, status and tests](../docs/freertos-motion-control.md).

Read [body control](../docs/body-control.md), [wiring](../docs/wiring.md), and [shared protocol](../docs/protocol/protocol.md). Do not flash or treat this skeleton as safety-ready.

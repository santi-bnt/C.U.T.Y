# C.U.T.Y STM32F401 Firmware

Owns real-time physical control: PWM, servo motion, head PAN/TILT, ears, future arms, body/base axes, IMU acquisition, PID feedback, and safety limits.

The current control hardware is an **STM32F401 Black Pill**, also targeted by the [carrier PCB v1.1](../hardware/electronics/kicad/cuty_carrier/README.md). Confirm the exact MCU suffix and board revision before generating firmware.

`Core/` and `Drivers/` are reserved for the STM32F401 board-specific CubeMX/startup and CMSIS/HAL project. No generated HAL, clock configuration or firmware build system is supplied yet. The carrier's UART/PWM/ADC pin assignments document the PCB design; firmware initialization and physical validation remain pending.

`App/` separates communication, servos, IMU, control, and safety. Every C/H file is a comment-only template, not firmware. Raspberry sends high-level targets; STM32 validates and converts them into safe movement.

Read [body control](../docs/body-control.md), [wiring](../docs/wiring.md), and [shared protocol](../docs/protocol/protocol.md). Do not flash or treat this skeleton as safety-ready.

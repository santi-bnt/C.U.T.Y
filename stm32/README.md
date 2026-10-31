# C.U.T.Y STM32H7 Firmware

Owns real-time physical control: PWM, servo motion, head PAN/TILT, ears, future arms, body/base axes, IMU acquisition, PID feedback, and safety limits.

`Core/` and `Drivers/` are reserved for a future selected STM32H7 board/CubeMX-generated project. No board, pinout, HAL, clock configuration, or build system has been guessed.

`App/` separates communication, servos, IMU, control, and safety. Every C/H file is a comment-only template, not firmware. Raspberry sends high-level targets; STM32 validates and converts them into safe movement.

Read [body control](../docs/body-control.md), [wiring](../docs/wiring.md), and [shared protocol](../docs/protocol/protocol.md). Do not flash or treat this skeleton as safety-ready.

# STM32 Servos

Planned active joints: head PAN, left arm and right arm. The five-output PCB retains two reserved channels.

Own PWM generation and calibrated goal-to-motion conversion under safety limits. Inputs are validated pose/axis goals, not a continuous Raspberry PWM stream. Calibration, channel assignment, neutral positions, slew limits, and actuator feedback are TBD.

`servo.c/.h` convert a normalized position to a pulse width. `calibration.c/.h` hold the per-joint table (default 1100–1900 µs, centre 1500 µs = assembly neutral, not yet bench-verified). TIM4 PWM lives in `Core/Src/board_f401.c`. Commanded positions are not measured positions. See [bring-up and calibration](../../../docs/freertos-motion-control.md#bring-up-on-the-real-robot).

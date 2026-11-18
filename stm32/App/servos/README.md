# STM32 Servos

Planned active joints: head PAN, left arm and right arm. The five-output PCB retains two reserved channels.

Own PWM generation and calibrated goal-to-motion conversion under safety limits. Inputs are validated pose/axis goals, not a continuous Raspberry PWM stream. Calibration, channel assignment, neutral positions, slew limits, and actuator feedback are TBD.

The C/H module now provides pure normalized-position-to-pulse conversion for caller-supplied endpoints. It does not initialize or update hardware PWM. Endpoint calibration and physical validation remain pending. Do not equate commanded positions with measured positions. See [motion architecture](../../../docs/freertos-motion-control.md).

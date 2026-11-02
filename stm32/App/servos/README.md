# STM32 Servos

Future channels: head PAN, head TILT, left ear, right ear, left arm, right arm, body/base X axis, body/base Y axis.

Own PWM generation and calibrated goal-to-motion conversion under safety limits. Inputs are validated pose/axis goals, not a continuous Raspberry PWM stream. Calibration, channel assignment, neutral positions, slew limits, and actuator feedback are TBD.

The C/H templates implement nothing. Do not equate commanded positions with measured positions unless feedback is available.

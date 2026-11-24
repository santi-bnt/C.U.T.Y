# STM32 Servos

Active profile-gated joints: HEAD_PAN, LEFT_ARM and RIGHT_ARM. The five-output PCB retains two reserved channels.

The board driver owns TIM4 PWM generation and calibrated goal-to-pulse conversion under safety limits. Inputs are validated axis goals, not a continuous Raspberry PWM stream. The user-reported carrier assignment is HEAD_PAN=PB6/J7, LEFT_ARM=PB7/J8 and RIGHT_ARM=PB8/J9; per-axis neutral, limits, direction, velocity and acceleration require confirmed calibration. There are no actuator position sensors.

The C/H module also validates profile data, binds the three PWM callbacks and enables output only in a profile build after explicit ARM/START. The default build keeps outputs disabled. Endpoint calibration and physical validation remain pending. Do not equate commanded positions with measured positions. See [motion architecture](../../../docs/freertos-motion-control.md).

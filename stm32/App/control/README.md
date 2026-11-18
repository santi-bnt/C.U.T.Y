# STM32 Control

The fixed version plans head PAN and left/right arm motion. Body/base movement is not part of this configuration.

Inputs: validated high-level target and calibrated IMU measurement. Outputs: servo goals through the servos/safety boundaries, plus target/measured/error telemetry.

`body_control.c/.h` now implement portable normalized setpoint filtering with position/velocity/acceleration limits and serialized safety transitions. `pid.c/.h` remain placeholders. Physical axis mapping, actuator coupling, gains, anti-windup and measured feedback remain pending. No IMU/body PID is implemented. See [actual status and tests](../../../docs/freertos-motion-control.md).

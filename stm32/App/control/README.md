# STM32 Control

Future head/ear/arm/body motion control and two-axis body PID. Body/base movement may use two servos and IMU feedback to regulate roll/pitch.

Inputs: validated high-level target and calibrated IMU measurement. Outputs: servo goals through the servos/safety boundaries, plus target/measured/error telemetry.

`body_control.c/.h` and `pid.c/.h` are empty comment-only templates. Axis mapping, gains, loop frequency, actuator coupling, saturation, anti-windup, and fault behavior require later design and testing. No PID math is implemented here.

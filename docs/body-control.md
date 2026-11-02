# Body Control Plan

STM32 owns head PAN/TILT, left/right ear, future left/right arm, body/base X/Y axes, IMU, two-axis PID, PWM, calibrated limits, and real-time safety.

Body roll/pitch control may use two servos and IMU feedback. Mechanical geometry, coupled kinematics, coordinate frames, sensor calibration, control frequency, gains, filtering, saturation/anti-windup, travel/rate limits, and safe fault behavior remain to be designed.

Raspberry requests high-level goals such as `SET_BODY,8,0` or `CENTER_BODY`; it must not continuously stream raw PWM. These examples do not fix angle units, signs, numeric bounds, or motion trajectories.

STM32 should eventually report target/measured/error for both PID axes and distinguish commanded servo position from measurement. The future dashboard plots telemetry only. All firmware files are placeholders; no servo or PID implementation exists.

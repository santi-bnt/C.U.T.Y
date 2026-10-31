# STM32 Safety

Future real-time enforcement of calibrated position/speed limits, command timeout policy, invalid input handling, startup neutral behavior, and sensor/actuator fault behavior.

All physical movement must pass STM32 safety checks. Sleep/wake or connection loss must not bypass limits. Actual safe states, thresholds, power interlocks, and recovery rules are TBD and require hardware review.

Templates are not a safety implementation.

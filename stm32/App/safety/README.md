# STM32 Safety

Future real-time enforcement of calibrated position/speed limits, command timeout policy, invalid input handling, startup neutral behavior, and sensor/actuator fault behavior.

All physical movement must pass STM32 safety checks. Sleep/wake or connection loss must not bypass limits. Actual safe states, thresholds, power interlocks, and recovery rules are TBD and require hardware review.

DISARMED/READY/ACTIVE/FAULT with a latched first fault reason (`CutyFaultReason`) and an external inhibit (low battery). Together with the task-liveness kill (`App/supervision`), the IWDG and the J3 switch, it forms four safety layers; physical validation is still pending. See [safety layers](../../../docs/freertos-motion-control.md#safety-layers).

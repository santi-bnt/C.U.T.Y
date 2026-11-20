# STM32 Supervision

`liveness.c/.h`: SafetyTask checks the ServoControlTask beat every 10 ms. A beat older
than 50 ms trips a latch. The board then kills the PWM pins and SafetyTask stops
refreshing the IWDG, so the MCU resets with outputs off.

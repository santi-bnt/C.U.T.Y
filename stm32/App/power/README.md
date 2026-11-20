# STM32 Power

`battery.c/.h`: 3S LiPo supervision from the carrier divider on PA1 (Vbat = Vadc × 122 / 22).
It applies a 10 Hz EMA filter. Below 5 V means "no pack"; below 9.9 V for 1 s latches
CRITICAL (motion inhibited) until the pack reads above 11.0 V for 2 s; below 10.5 V is a
warning. Pure logic: SafetyTask feeds it millivolts.

# STM32 Control

The fixed version plans head PAN and left/right arm motion. Body/base movement is not part of this configuration.

Inputs: validated high-level target and calibrated IMU measurement. Outputs: servo goals through the servos/safety boundaries, plus target/measured/error telemetry.

`fir_filter.c/.h` provide a fixed-buffer, sample-by-sample FIR. `body_control.c/.h` apply a five-tap moving average to HEAD_PAN once per nominal 20 ms tick before the existing velocity/acceleration-limited trajectory; LEFT_ARM and RIGHT_ARM retain their current path. A/B enable is serialized and primes filter history to the current target. Existing safety states reset stale filter history. This portable core remains dry-run; there is no UART adapter, physical PWM or flashable image. `pid.c/.h` remain placeholders. See [FIR DSP and tests](../../../docs/digital-signal-processing-fir.md) and [motion architecture](../../../docs/freertos-motion-control.md).

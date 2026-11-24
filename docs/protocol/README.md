# C.U.T.Y Shared Contracts

Historical and shared-contract documents for Raspberry ↔ STM32 ↔ telemetry consumers. The active experimental V2 implementation is documented in [firmware motion control](../freertos-motion-control.md), [hardware bridge](../../raspberry/src/cuty/hardware/README.md) and [calibration](../servo-calibration.md). The examples in `commands.md` are proposals and are not accepted by the V2 parser.

V2 UART transport, named-axis targets and profile-gated physical firmware are
implemented separately from these legacy examples. Physical calibration and
assembled-system validation remain pending. The current axes are HEAD_PAN,
LEFT_ARM and RIGHT_ARM; body and gimbal targets are superseded.

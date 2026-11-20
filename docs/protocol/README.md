# C.U.T.Y Shared Contracts

Hardware-independent design documents for Raspberry ↔ STM32 ↔ telemetry consumers. [Protocol](protocol.md), [commands](commands.md), and [telemetry](telemetry.md) are proposals, not implemented or stable contracts. Keep board drivers and UI code out of this folder.

The implemented contract is **V2**, documented with the firmware in
[freertos-motion-control.md](../freertos-motion-control.md#wire-protocol-v2) and spoken by
`raspberry/src/cuty/hardware/stm32_bridge.py`. The examples in this folder are earlier
proposals kept for history. Axes: HEAD_PAN, LEFT_ARM and RIGHT_ARM; body and gimbal
targets are superseded.

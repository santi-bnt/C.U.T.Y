# C.U.T.Y Shared Contracts

Hardware-independent design documents for Raspberry ↔ STM32 ↔ telemetry consumers. [Protocol](protocol.md), [commands](commands.md), and [telemetry](telemetry.md) are proposals, not implemented or stable contracts. Keep board drivers and UI code out of this folder.

The new [experimental V2 dry-run parser](../freertos-motion-control.md) is separate
from these legacy examples. It uses normalized single-axis targets; physical
Raspberry/STM32 transport is not implemented. The current mechanical axes are
HEAD_PAN, LEFT_ARM and RIGHT_ARM; body and gimbal targets are superseded.

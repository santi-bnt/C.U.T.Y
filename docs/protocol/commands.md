# Proposed High-Level Commands

Status: table below is historical and not accepted by the implemented experimental V2 parser. V2 commands are documented in [motion control](../freertos-motion-control.md). No physical PWM or STM32 UART driver is implemented in stage 1.

| Example | Proposed intent |
| --- | --- |
| `SET_HEAD_PAN,15` | Illustrative head PAN goal; units/signs pending calibration |
| `SET_LEFT_ARM,8` | Illustrative left arm goal; units/signs pending calibration |
| `SET_RIGHT_ARM,-8` | Illustrative right arm goal; units/signs pending calibration |
| `SET_EARS,20,20` | Left/right ear goals |
| `SLEEP` | Request a safe low-activity state, semantics TBD |
| `WAKE` | Request resumption after safety checks, semantics TBD |

No raw PWM command is proposed. Numeric examples are not validated physical limits. Ranges, units, timing, acknowledgements, and rejection rules belong to a later protocol/control task. Old `SET_HEAD` PAN/TILT and `SET_BODY` proposals belonged to the superseded gimbal variant and are not active.

# Proposed High-Level Commands

Status: historical examples. The implemented commands are `V2,HB`, `V2,ARM`, `V2,START`, `V2,DISARM`, `V2,RESET` and `V2,TARGET,<joint>,<milli>`; see [the firmware doc](../freertos-motion-control.md#wire-protocol-v2). Raspberry/behavior produces goals; STM32 is intended to own trajectories, PWM and safety for three active joints. The base, pedestal and torso are fixed.

| Example | Proposed intent |
| --- | --- |
| `SET_HEAD_PAN,15` | Illustrative head PAN goal; units/signs pending calibration |
| `SET_LEFT_ARM,8` | Illustrative left arm goal; units/signs pending calibration |
| `SET_RIGHT_ARM,-8` | Illustrative right arm goal; units/signs pending calibration |
| `SET_EARS,20,20` | Left/right ear goals |
| `SLEEP` | Request a safe low-activity state, semantics TBD |
| `WAKE` | Request resumption after safety checks, semantics TBD |

No raw PWM command is proposed. Numeric examples are not validated physical limits. Ranges, units, timing, acknowledgements, and rejection rules belong to a later protocol/control task. Old `SET_HEAD` PAN/TILT and `SET_BODY` proposals belonged to the superseded gimbal variant and are not active.

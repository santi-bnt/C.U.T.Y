# Proposed High-Level Commands

Status: examples only; nothing is implemented. Raspberry/behavior produces goals; STM32 owns motion, PWM, PID, and safety.

| Example | Proposed intent |
| --- | --- |
| `SET_HEAD,15,-4` | Head PAN/TILT goal; example angles, units/signs pending calibration |
| `SET_BODY,8,0` | Two-axis body goal; mapping to roll/pitch or X/Y remains to be agreed |
| `SET_EARS,20,20` | Left/right ear goals |
| `CENTER_BODY` | Request a calibrated neutral body target |
| `SLEEP` | Request a safe low-activity state, semantics TBD |
| `WAKE` | Request resumption after safety checks, semantics TBD |

Future arms can add high-level commands after mechanical/control design. No raw PWM command is proposed. Numeric examples are not validated physical limits. Ranges, units, timing, acknowledgements, and rejection rules belong to a later protocol/control task.

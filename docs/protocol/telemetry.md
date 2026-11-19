# Proposed Telemetry

Status: illustrative records, not implemented or stable. Current design has a fixed base/body and only HEAD_PAN, LEFT_ARM and RIGHT_ARM; the older Nido gimbal/body telemetry is superseded.

| Example | Proposed meaning |
| --- | --- |
| `HEAD_PAN,14.8` | Illustrative commanded PAN target; units/signs and measured-vs-commanded contract pending |
| `LEFT_ARM,14.8` | Illustrative commanded arm target; units/signs and measured-vs-commanded contract pending |
| `RIGHT_ARM,-14.8` | Illustrative commanded arm target; units/signs and measured-vs-commanded contract pending |
| `BATTERY,82` | Battery percentage example; sensing/estimation not selected |
| `STATUS,OK` | Firmware status example; status/fault vocabulary pending |

Future trajectory telemetry should expose target and commanded position per active joint; no body PID or IMU stabilization is part of the current design. Add timestamps, validity, sequence/version, and units in a later contract review. Historical Nido examples (`IMU`, `HEAD` PAN/TILT and `BODY`) are not active definitions.

Raspberry will aggregate STM32 reports with online/offline, CPU/temp, LLM local/cloud status, camera/detection/target, current expression, and logs for the web dashboard. Telemetry is observation, not a dashboard-driven real-time PID loop.

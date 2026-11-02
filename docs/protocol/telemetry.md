# Proposed Telemetry

Status: illustrative records, not implemented or stable.

| Example | Proposed meaning |
| --- | --- |
| `IMU,7.8,-0.2` | Two-axis orientation; roll/pitch units/frame pending agreement |
| `HEAD,14.8,-4.1` | PAN/TILT state; distinguish commanded from measured before implementation |
| `BODY,7.9,0.1` | Two-axis body state; coordinate mapping pending |
| `BATTERY,82` | Battery percentage example; sensing/estimation not selected |
| `STATUS,OK` | Firmware status example; status/fault vocabulary pending |

Future PID telemetry should expose target, measured value, and error per axis; servo telemetry must label estimated/commanded versus measured positions. Add timestamps, validity, sequence/version, and units in a later contract review.

Raspberry will aggregate STM32 reports with online/offline, CPU/temp, LLM local/cloud status, camera/detection/target, current expression, and logs for the web dashboard. Telemetry is observation, not a dashboard-driven real-time PID loop.

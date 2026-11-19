# STM32 IMU

Future sensor initialization, acquisition, calibration, orientation estimation, timestamps, and validity reporting. This placeholder is not connected to the fixed-base motion task. If retained for future diagnostics, its outputs may feed telemetry; it does not stabilize or move the body.

No sensor model, driver, sample rate, or coordinate frame is selected. imu.h declares only a future timestamped sample/read interface; imu.c remains a TODO. No task or PID is created. The Raspberry and web dashboard may eventually consume reported measurements; they do not own the real-time feedback loop.

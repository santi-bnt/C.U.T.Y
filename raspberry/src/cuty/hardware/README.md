# C.U.T.Y Hardware Bridge

Future Raspberry-to-STM32 boundary. `stm32_bridge.py` and `robot_commands.py` are TODO-only placeholders: no UART driver, command serialization, or hardware action exists.

Inputs: high-level behavior goals, such as head pose, body target, ears, sleep/wake. Outputs: proposed UART commands; received telemetry feeds brain/status and the future telemetry service.

Raspberry must NOT continuously send raw servo PWM. STM32 owns PWM generation, conversion to physical motion, limits, IMU feedback, PID, and real-time safety.

See [shared protocol](../../../../docs/protocol/protocol.md), [commands](../../../../docs/protocol/commands.md), and [telemetry](../../../../docs/protocol/telemetry.md). Electrical settings and the wire contract require a separate reviewed task.

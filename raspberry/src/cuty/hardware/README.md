# C.U.T.Y Hardware Bridge

Future Raspberry-to-STM32 boundary. `stm32_bridge.py` and `robot_commands.py` are TODO-only placeholders: no UART driver, command serialization, or hardware action exists.

Inputs: high-level behavior goals for HEAD_PAN, LEFT_ARM and RIGHT_ARM, plus non-motion states such as sleep/wake. The base, pedestal and torso are fixed. Outputs: proposed UART commands; received telemetry feeds brain/status and the future telemetry service.

Raspberry must NOT continuously send raw servo PWM. STM32 is intended to own PWM generation, commanded-position limits, trajectories and real-time safety for the three active servos. There is no body stabilization PID or active IMU feedback in the fixed-base design. Hardware integration and output validation are pending.

See [shared protocol](../../../../docs/protocol/protocol.md), [commands](../../../../docs/protocol/commands.md), and [telemetry](../../../../docs/protocol/telemetry.md). Electrical settings and the wire contract require a separate reviewed task.

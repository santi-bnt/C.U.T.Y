# C.U.T.Y Hardware Bridge

Para medir un servo desde una terminal interactiva de la Pi, consulta el
[modo de calibración manual](../../../../docs/servo-calibration.md) y ejecuta
`python -m cuty.hardware.servo_calibration --help`. Necesita el firmware de
calibración y una confirmación explícita antes de activar el primer pulso.

Stage 1 diagnostic Raspberry-to-STM32 boundary. `stm32_bridge.py` provides an opt-in CLI and `robot_commands.py` serializes the existing experimental V2 LF-framed commands. It opens no port until explicitly invoked, sends no ARM/START on connection, and never starts movement automatically. Install `pyserial` with `python3 -m pip install pyserial`; run `python3 -m cuty.hardware.stm32_bridge --port /dev/serial0 status` (or set `CUTY_STM32_PORT`). Device names vary; inspect `/dev/serial*` and configure GPIO14/15 UART in Raspberry Pi OS. The port should be owned by one process; Linux uses an advisory lock under `/run/lock`.

`raspberry/scripts/servos_uart.py` belongs to the superseded PING/STOP/SERVO test and is not compatible with the V2 firmware. Use `servo_calibration` for manual physical testing and `stm32_bridge status` for diagnostics.

Inputs: explicit high-level behavior goals for HEAD_PAN, LEFT_ARM and RIGHT_ARM. The base, pedestal and torso are fixed. `robot_motion.py` serializes goals through the shared V2 bridge; motion stays disabled until a validated per-axis profile and explicit physical-enable configuration are present.

`CUTY_ROBOT_MODE` selects the application mode at startup: `simulation` is the default, accepts voice actions into virtual commanded references, and never opens UART; enable read-only telemetry to show those references in the web status view. `test` requires a complete confirmed profile, a live DISARMED link and `CUTY_TEST_AXIS`, and accepts only allowlisted actions for that axis. `robot` uses the complete profile and enables the full action allowlist and optionally face following. `MotionActionGate.select_simulation()` disarms and closes an existing executor. The separate `servo_calibration` command is the manual calibration test: one selected axis, explicit `--confirm-unloaded`, small 10 us increments, and no automatic sweep. It does not count as profile confirmation.

The voice allowlist includes stop, single-axis head/arm goals, left/right/both-arm waves, and `greet_right` (“saluda y mira a la derecha”). That greeting moves HEAD_PAN and both arms in one trajectory using small normalized references, then returns them to their calibrated centers. A requested wave/greeting also sets the happy face expression; expression-only model calls never request body motion.

Raspberry must NOT continuously send raw servo PWM. The STM32 owns PWM generation, configured pulse limits, trajectories and local safety for the three active servos in a profile build. There is no body stabilization PID or active IMU feedback in the fixed-base design. Final calibrated profile and assembled-robot validation remain pending.

The STM32 project implements HAL UART, ACK/NACK, diagnostic telemetry, FreeRTOS trajectory control and calibrated three-channel PWM callbacks. The default build blocks PWM; `--profile` enables configured automatic output only after the JSON calibration is complete. `--calibration` remains a separate one-axis manual mode. The executor checks DISARMED on connection and never arms on startup or reconnection. See [shared protocol](../../../../docs/protocol/protocol.md), [commands](../../../../docs/protocol/commands.md), [telemetry](../../../../docs/protocol/telemetry.md), and [calibration](../../../../docs/servo-calibration.md).

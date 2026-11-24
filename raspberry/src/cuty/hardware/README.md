# C.U.T.Y Hardware Bridge

Para medir un servo desde una terminal interactiva de la Pi, consulta el
[modo de calibración manual](../../../../docs/servo-calibration.md) y ejecuta
`python -m cuty.hardware.servo_calibration --help`. Necesita el firmware de
calibración y una confirmación explícita antes de activar el primer pulso.

Stage 1 diagnostic Raspberry-to-STM32 boundary. `stm32_bridge.py` provides an opt-in CLI and `robot_commands.py` serializes the existing experimental V2 LF-framed commands. It opens no port until explicitly invoked, sends no ARM/START on connection, and never starts movement automatically. Install `pyserial` with `python3 -m pip install pyserial`; run `python3 -m cuty.hardware.stm32_bridge --port /dev/serial0 status` (or set `CUTY_STM32_PORT`). Device names vary; inspect `/dev/serial*` and configure GPIO14/15 UART in Raspberry Pi OS. The port should be owned by one process; Linux uses an advisory lock under `/run/lock`.

`raspberry/scripts/servos_uart.py` belongs to the superseded PING/STOP/SERVO test and is not compatible with the V2 firmware. Use `servo_calibration` for manual physical testing and `stm32_bridge status` for diagnostics.

Inputs: high-level behavior goals for HEAD_PAN, LEFT_ARM and RIGHT_ARM, plus non-motion states such as sleep/wake. The base, pedestal and torso are fixed. Outputs: proposed UART commands; received telemetry feeds brain/status and the future telemetry service.

Raspberry must NOT continuously send raw servo PWM. STM32 is intended to own PWM generation, commanded-position limits, trajectories and real-time safety for the three active servos. There is no body stabilization PID or active IMU feedback in the fixed-base design. Hardware integration and output validation are pending.

The STM32 project now implements HAL UART, ACK/NACK and diagnostic telemetry. Its normal build blocks PWM; the separate calibration build can drive one manual channel while READY. Automatic TARGET motion remains unbound. V2 is the code reference; legacy `SET_*` docs are historical design sketches, not supported commands. See [shared protocol](../../../../docs/protocol/protocol.md), [commands](../../../../docs/protocol/commands.md), and [telemetry](../../../../docs/protocol/telemetry.md).

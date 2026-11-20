# C.U.T.Y Hardware Bridge

Raspberry-to-STM32 boundary. `stm32_bridge.py` speaks the V2 line protocol of the FreeRTOS firmware: 10 Hz heartbeat, `ARM`/`START`/`TARGET`, and parsing of `BOOT`, `ACK`/`NAK`, `TEL` and `DIAG`. It also has a bench console: `python -m cuty.hardware.stm32_bridge --port /dev/serial0`. Nothing runs on import, and `head_follow.py` is not connected to it yet. `robot_commands.py` is still a placeholder.

Inputs: high-level behavior goals for HEAD_PAN, LEFT_ARM and RIGHT_ARM, plus non-motion states such as sleep/wake. The base, pedestal and torso are fixed. Outputs: proposed UART commands; received telemetry feeds brain/status and the future telemetry service.

Raspberry must NOT continuously send raw servo PWM. STM32 is intended to own PWM generation, commanded-position limits, trajectories and real-time safety for the three active servos. There is no body stabilization PID or active IMU feedback in the fixed-base design. Hardware integration and output validation are pending.

Wire contract and bring-up: [FreeRTOS firmware](../../../../docs/freertos-motion-control.md#wire-protocol-v2).

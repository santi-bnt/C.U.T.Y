# Architecture and Ownership

| Domain | Owner | Boundary |
| --- | --- | --- |
| AI/LLM, conversation, speech | Raspberry Pi 5 | brain, llm, audio |
| Camera, face detection/tracking | Raspberry Pi 5 | vision produces normalized targets |
| Eyes, pupils, mouth, expressions, screen | Raspberry Pi 5 | face renders only |
| High-level behavior | Raspberry Pi 5 | brain consumes targets, requests goals |
| UART bridge and telemetry server | Raspberry Pi 5 | hardware and telemetry |
| PWM, servos, physical movement | STM32H7 | servos/control with safety |
| IMU, PID, real-time limits | STM32H7 | imu/control/safety |
| Dashboard and digital twin | Web | consumes aggregated telemetry |
| Mechanical sources | CAD | native SolidWorks files |
| PCB sources | Electronics | native KiCad files |

## Target flow

Camera → detector → tracker → normalized X/Y target.
- face consumes it for pupil rendering.
- future brain/behavior consumes it for head goals → hardware bridge → UART → STM32 motion/safety.
- STM32 IMU → STM32 body PID → servos/safety; measurements feed telemetry.
- Raspberry audio and LLM → speaking state/expression → face (future visual integration).
- Raspberry aggregates subsystem and STM32 status for web observation.

Never let vision/face/dashboard generate PWM or move the real-time feedback loop into Raspberry. Keep AI expression tool events distinct from UART records.

## Current versus planned

Current: standalone Raspberry touchscreen menu/demo face/Wi-Fi imported from GitHub; desktop CLI audio conversation, Gemini default and OpenAI adapter, web lookup, session context, language instructions, Spanish thinking clips, state machine, expression events/console sink.

Planned: Pi hardware validation, local LLM fallback, standalone STT/TTS, a reusable face renderer connected to voice, camera/detection/tracking, persistent memory/behavior, bridge/protocol implementation, telemetry server, STM32 firmware, dashboard, CAD, PCB.

Python TODO modules and C/H comment templates define locations only; they are not fake functional interfaces. Existing dependencies and provider selection are preserved. The [migration inventory](reorganization.md) explains compatibility and untouched local files.

## Compact repository

Five main areas: `raspberry/`, `stm32/`, `hardware/` (CAD/electronics), `web/`, and `docs/` (including `protocol/`). Setup scripts live in `raspberry/scripts/`. Root Python/shell wrappers exist only to preserve old launch commands and services, not duplicate implementation.

# Architecture and Ownership

| Domain | Owner | Boundary |
| --- | --- | --- |
| AI/LLM, conversation, speech | Raspberry Pi 5 | brain, llm, audio |
| Camera, face detection/tracking | Raspberry Pi 5 | vision produces normalized targets |
| Eyes, pupils, mouth, expressions, screen | Raspberry Pi 5 | face renders only |
| High-level behavior | Raspberry Pi 5 | brain consumes targets, requests goals |
| UART bridge and telemetry server | Raspberry Pi 5 | hardware and telemetry |
| PWM, servos, physical movement | STM32F401 Black Pill | servos/control with safety; firmware pending |
| IMU, PID, real-time limits | STM32F401 Black Pill | imu/control/safety; firmware pending |
| Dashboard and digital twin | Web | consumes aggregated telemetry |
| Mechanical sources | CAD | native SolidWorks files |
| PCB sources | Electronics | native KiCad files |

## Target flow

Camera → detector → tracker → normalized X/Y target.
- face consumes it for pupil rendering.
- future brain/behavior consumes it for head goals → hardware bridge → UART → STM32 motion/safety.
- STM32 IMU → STM32 body PID → servos/safety; measurements feed telemetry.
- Raspberry audio and LLM → expression + lip-sync level over local UDP → face.
- Raspberry aggregates subsystem and STM32 status for web observation.

Never let vision/face/dashboard generate PWM or move the real-time feedback loop into Raspberry. Keep AI expression tool events distinct from UART records.

## Current versus planned

Implemented: Raspberry touchscreen menu/Wi-Fi and animated face (eyes, blinks, mouth, expressions, camera targets and lip sync); camera capture, face detection and visual tracking; CLI audio conversation and Gemini hands-free sessions started by the menu, web lookup, session context, language instructions, Spanish thinking clips and state machine. OpenAI remains optional for the keyboard CLI.

Hardware observations: ReSpeaker capture/playback and Gemini replies were tested on the Pi; the SPI screen, touchscreen and camera initialization have also been observed. Stable operation, the reported intermittent screen/restart issues, end-to-end gaze tracking and lip-sync timing still need validation. Implemented code does not imply that these checks are complete; see the [roadmap](roadmap.md).

PCB design: [carrier v1.1](../hardware/electronics/kicad/cuty_carrier/README.md) includes native KiCad sources, Gerbers, BOM and schematic exports for Pi 5, STM32F401 Black Pill, Display-G, ReSpeaker and five servo connectors. Fabrication, assembly, electrical validation and integration with firmware remain pending.

Planned: local LLM fallback, standalone STT/TTS, face recognition, persistent memory/behavior, bridge/protocol implementation, telemetry server, STM32F401 firmware, dashboard and mechanical design.

Python TODO modules and C/H comment templates define locations only; they are not fake functional interfaces. Existing dependencies and provider selection are preserved. The [migration inventory](reorganization.md) explains compatibility and untouched local files.

## Compact repository

Five main areas: `raspberry/`, `stm32/`, `hardware/` (CAD/electronics), `web/`, and `docs/` (including `protocol/`). Setup scripts live in `raspberry/scripts/`. Root Python/shell wrappers exist only to preserve old launch commands and services, not duplicate implementation.

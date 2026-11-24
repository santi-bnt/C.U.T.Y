# Architecture and Ownership

The [Black Pill firmware](../stm32/blackpill_uart/README.md), Raspberry UART owner, named-joint motion actions, face-follow IPC adapter and read-only telemetry path are implemented. Their software tests and builds do not certify the assembled robot; final per-axis calibration and supervised physical validation remain pending.

| Domain | Owner | Boundary |
| --- | --- | --- |
| AI/LLM, conversation, speech | Raspberry Pi 5 | brain, llm, audio |
| Camera, face detection/tracking | Raspberry Pi 5 | vision produces normalized targets |
| Eyes, pupils, mouth, expressions, screen | Raspberry Pi 5 | face renders only |
| High-level behavior | Raspberry Pi 5 | allowlisted behavior requests named-joint goals through the motion gate |
| UART bridge and telemetry server | Raspberry Pi 5 | sole UART owner, V2 commands/ACKs, reconnect without rearming, optional read-only local status API |
| PWM, servos, physical movement | STM32F401 Black Pill | FreeRTOS trajectories and three calibrated PWM channels in profile builds |
| IMU, body PID | STM32F401 Black Pill | not active; fixed-base robot has no configured IMU loop |
| Dashboard and digital twin | Web | local visualization; status API is not connected by default |
| Mechanical sources | CAD | native SolidWorks files |
| PCB sources | Electronics | native KiCad files |

## Target flow

Camera → detector → tracker → normalized X/Y target.

- Face consumes it for pupil rendering.
- Optional head following consumes the same target through a bounded PID → local Unix socket → sole UART owner → V2 → STM32. Physical following requires explicit opt-in, a confirmed profile, a live DISARMED link and a manual touchscreen action to arm.
- Voice/behavior requests pass through an explicit action allowlist and the shared motion gate/executor → UART → STM32. Simulation is the default and does not open UART.
- Future IMU data may feed diagnostics after sensor selection and calibration. Body PID is outside the current fixed-base three-joint configuration.
- Raspberry audio and LLM → expression + lip-sync level over local UDP → face.
- Raspberry can aggregate subsystem and STM32 status for read-only web observation.

Vision, face rendering and the dashboard never generate PWM. Keep AI expression tool events distinct from UART records.

## Current versus planned

Implemented: Raspberry touchscreen menu/Wi-Fi and animated face; camera capture, face detection and visual tracking; voice conversation and Gemini hands-free sessions; UART V2 bridge, named-axis independent and coordinated goals, cancellation/stop, simulation/test/robot gates, voice action allowlist, one-axis manual calibration, generated-profile firmware build, optional physical head-follow adapter and read-only telemetry.

Hardware observations: ReSpeaker capture/playback and Gemini replies were tested on the Pi; the SPI screen, touchscreen and camera initialization have also been observed. The user reports physical Pi-to-STM32 UART communication and movement on all three servo channels. Stable operation, end-to-end gaze tracking, calibration and integrated behavior still require the supervised sequence in the [physical validation guide](robot-validation.md). Software tests and builds do not count as those checks.

PCB design: [carrier v1.1](../hardware/electronics/kicad/cuty_carrier/README.md) includes native KiCad sources, Gerbers, BOM and schematic exports for Pi 5, STM32F401 Black Pill, Display-G, ReSpeaker and five servo connectors. Fabrication, assembly and electrical validation of the carrier remain pending.

Implemented in software: consent-based local face templates and unknown-safe matching, plus on-demand still-image description through the existing Gemini key/session voice path. SFace model installation, threshold calibration, dashboard connection to live telemetry and physical integration tests remain pending; see [vision privacy/setup](face-vision.md). Planned: local LLM fallback, standalone STT/TTS, persistent memory/behavior and IMU/body control.

Python TODO modules and C/H comment templates define locations only; they are not functional interfaces. Existing dependencies and provider selection are preserved. The [migration inventory](reorganization.md) explains compatibility and untouched local files.

## Compact repository

Five main areas: `raspberry/`, `stm32/`, `hardware/` (CAD/electronics), `web/`, and `docs/` (including `protocol/`). Setup scripts live in `raspberry/scripts/`. Root Python/shell wrappers exist only to preserve old launch commands and services, not duplicate implementation.

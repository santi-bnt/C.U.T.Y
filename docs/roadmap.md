# Roadmap

Status reviewed on 2026-11-04. Checked implementation items mean code or design files exist; they do not certify hardware reliability or electrical safety. Physical checks are listed separately. Current targets are Raspberry Pi 5 and STM32F401 Black Pill.

## Phase 1 — Brain

- [x] Voice conversation (desktop push-to-talk)
- [x] Online LLM (Gemini default; OpenAI optional)
- [x] Gemini hands-free conversation launched from the touchscreen menu
- [x] Spoken return to the menu, web lookup, session context and expression tools
- [x] Basic ReSpeaker capture/playback and Gemini replies tested on Raspberry Pi
- [ ] Sustained Pi runtime validation: listening sensitivity, screen stability, restart/network diagnosis and audio levels
- [ ] Wake-name interruption while C.U.T.Y is speaking
- [ ] Local LLM fallback

## Phase 2 — Face

- [x] Eyes and pupil rendering (`face/eyes.py`, `face/renderer.py`)
- [x] Blink and idle animation (`face/animations.py`)
- [x] Mouth rendering (`face/mouth.py`)
- [x] Expressions integrated with the screen and conversation state
- [x] Speaking animation / lip sync (`audio/lipsync.py`, `face/link.py`)
- [ ] Sustained physical display validation and lip-sync latency tuning

## Phase 3 — Vision

- [x] Raspberry Pi / USB camera capture adapters (`vision/camera.py`)
- [x] Face detection with YuNet and Haar fallback (`vision/face_detector.py`)
- [x] Target selection, smoothing and lost-target handling (`vision/face_tracker.py`)
- [x] Visual eye tracking connected to the animated face
- [ ] End-to-end physical camera/detector/gaze validation (camera startup has been observed)
- [ ] Physical head tracking through STM32 goals and servos

## Phase 4 — STM32F401 Firmware

- [ ] Board-specific startup, clock configuration and HAL/CMSIS project for the Black Pill
- [ ] UART protocol implementation and validated Pi-to-STM32 link
- [ ] Servo control
- [ ] IMU
- [ ] Head movement
- [ ] Body PID

The files under `stm32/App/` are comment-only templates, not working firmware. Carrier pin assignments do not replace firmware implementation or physical tests.

## Phase 5 — Electronics and Mechanical Design

- [x] Carrier PCB v1.1 for Pi 5, STM32F401 Black Pill, Display-G, ReSpeaker and five servo connectors
- [x] Native KiCad sources, schematic/BOM exports and Gerbers in `hardware/electronics/kicad/cuty_carrier/`
- [ ] Review the saved DRC report's silkscreen warnings and reproduce checks with KiCad
- [ ] Fabrication, assembly, power validation and electrical integration

- [ ] Body
- [ ] Base
- [ ] Head
- [ ] Arms
- [ ] Internal assembly

## Phase 6 — Dashboard

- [ ] Telemetry
- [ ] PID graphs
- [ ] Digital twin

The `web/` directories currently contain documentation/placeholders.

## Phase 7 — Recognition

- [ ] Face registration
- [ ] Face recognition
- [ ] Person identity

Face detection/tracking is implemented; identifying who a person is remains separate future work. Hardware-specific design, protocol review and safety acceptance must precede motion tests.

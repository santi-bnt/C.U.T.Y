# Roadmap

Status reviewed on 2026-11-24. Checked implementation items mean code or design files exist; they do not certify hardware reliability or electrical safety. Physical checks are listed separately. Current targets are Raspberry Pi 5 and STM32F401 Black Pill.

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
- [x] Local consent-based face enrollment/matching and request-only Gemini image descriptions (software; SFace model and Pi validation pending)
- [ ] End-to-end physical camera/detector/gaze validation (camera startup has been observed)
- [x] Optional face-follow path through a local socket, the sole UART owner and STM32 goals (software; physical validation pending)

## Phase 4 — STM32F401 Firmware

- [x] Board-specific startup, clock configuration and HAL/CMSIS project for the Black Pill
- [x] UART V2 protocol, ACK/NACK and Raspberry link implementation (user reports physical link; supervised recheck pending)
- [x] Three-servo control integration: HEAD_PAN, LEFT_ARM, RIGHT_ARM (profile-gated; per-axis calibration pending)
- [x] HEAD_PAN low-pass FIR integration into the board FreeRTOS task
- [ ] Per-axis calibration, profile review and supervised UART/timer/PWM hardware validation

Portable parsing, trajectory control, safety logic, the CMSIS-RTOS2 adapter and HAL UART/PWM callbacks exist under `stm32/App/`, `stm32/Board/` and `stm32/blackpill_uart/`. Separate normal, manual-calibration, bench and profile-gated physical builds are available. See [implementation boundary and tests](freertos-motion-control.md). The [19-stage validation guide](robot-validation.md) tracks the remaining physical profile and system checks.

## Phase 5 — Electronics and Mechanical Design

- [x] Carrier PCB v1.1 for Pi 5, STM32F401 Black Pill, Display-G, ReSpeaker and five servo connectors
- [x] Native KiCad sources, schematic/BOM exports and Gerbers in `hardware/electronics/kicad/cuty_carrier/`
- [ ] Review the saved DRC report's silkscreen warnings and reproduce checks with KiCad
- [ ] Fabrication, assembly, power validation and electrical integration

- [x] Fixed pedestal/base and fixed torso CAD variant (`carcasa_v17_fija`, 27 STL)
- [x] Head PAN and two arm joints represented in the fixed CAD; fit/motion not physically validated
- [ ] Internal assembly and physical fit validation

## Phase 6 — Dashboard

- [x] Optional read-only Raspberry status API for connection, safety state and commanded targets
- [ ] Three-axis telemetry
- [ ] Digital twin

The website contains the fixed CAD reference, FreeRTOS motion explanation and local FIR demonstrations. The static dashboard is not connected to the Raspberry telemetry API or actuators; remote control remains disabled.

## Phase 7 — Recognition validation

- [x] Consent-gated local enrollment flow, embedding-only storage and unknown-safe matching (software)
- [ ] Install compatible OpenCV-contrib/SFace model on the Pi
- [ ] Calibrate match threshold/margin with consented samples and non-matches
- [ ] Validate local voice/camera/display/audio operation and resource use on the robot

Face matching identifies only a voluntarily registered local profile; it does not perform general identity recognition. The current matcher fails closed until YuNet landmarks and a compatible local SFace model are available. Hardware-specific design, protocol review and safety acceptance must precede motion tests.

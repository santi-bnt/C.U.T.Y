# Current configuration update

Three axes are supported: HEAD_PAN (J7), LEFT_ARM (J8), RIGHT_ARM (J9). J10 and
J11 are reserved. Protocol V2 accepts named axes only. The CubeIDE project at
[`stm32/blackpill_uart`](../stm32/blackpill_uart/README.md) links this portable
application to the STM32F401 HAL and FreeRTOS. USART2 receives V2 frames and returns
ACK/NACK, STATE and TELEM records. The default build keeps PWM disconnected; the
profile build links calibrated outputs to the motion tasks. Targets are normalized
software units, not calibrated angles.

# FreeRTOS / Motion Control

## Actual implementation boundary

The portable C modules implement byte-stream framing, strict V2 command parsing, three
normalized setpoints, bounded trajectories, heartbeat checks, a latched safety state
machine, and pulse-width conversion. The board layer initializes USART2, TIM4 and UART
RX. The default build leaves PWM disabled. A separate `build.py --profile` image binds
all three PWM callbacks using a validated per-axis profile; it still starts DISARMED
with outputs off until explicit ARM and START. Raspberry supplies the matching profile,
heartbeat, high-level gestures and guarded face-follow goals. `V2,INFO` reports the
SHA-256 fingerprint generated from the same profile JSON. The Raspberry executor
requires an exact match while the STM32 is DISARMED before authorizing physical control;
default, bench and calibration firmware report `none`. The handshake verifies profile
identity, not the physical calibration or safety of the assembled robot. IMU remains an
interface declaration; PID is not part of the fixed-base motion path.

The interactive website retains its scripted architecture visualization. A separately
configured read-only HTTP transport can display Raspberry/STM32 status and commanded
positions; it cannot send motion commands. Physical output and loaded-profile match are
shown as unverified until confirmed on hardware.

## Ownership and tasks

Pi 5 retains FaceTracker, visual errors, Gemini Live, voice and behavior/planning.
STM32 is intended to own local motion and timing. FreeRTOS scheduling separates these
responsibilities; hardware timers, never task delays, generate PWM.

| Task | CMSIS priority | Activation proposal | Stack budget (bytes) | Responsibility |
| --- | --- | --- | --- | --- |
| CommunicationTask | AboveNormal | RX event, batch <=64 bytes then yield 1 tick | 1536 | Frame/validate input, coalesce targets, queue control events |
| ServoControlTask | High | Poll 10 ms; trajectory update 20 ms | 1536 | Sole controller-state owner; apply events, safety and trajectory |
| SafetyTask | High1 | Absolute 10 ms deadline | 768 | Supervision notification, no shared state writes |
| DiagnosticsTask | Low | 200 ms / <=5 Hz | 1024 | Copy snapshots to bounded TX queue |
| IMUTask | TBD | No task created | 0 | Future sensor interface |

These are budgets, not measured execution times or proven priorities. The initial safety
thread only requests supervision: the sole control owner enforces heartbeat and limits on
its 10 ms poll. It is NOT an independent safety monitor if that owner stalls.
An independently validated task-liveness watchdog is still required before physical use.
All loops block/yield; ISR work is a queue put plus optional error flag, not parsing/logging.
No mutex is needed for the single-owner controller. Queue messages copy snapshots.
FreeRTOS syscall-safe IRQ priority is mandatory for the RX hook.

RTOS resources:

- RX: 256 timestamped byte entries (typically 2048 B on ARM), not a 256-byte DMA ring.
- Control events: 8 envelopes; targets: three one-entry mailboxes, one per joint; the latest goal wins per joint.
  Each message commands one joint; a coordinated atomic pose is not implemented.
- Snapshot and telemetry queues: one controller snapshot each; replies: eight entries.
- Approximate queue payload <4 KiB, four stacks 4864 B; control blocks, allocator,
  idle/timer stacks, driver/DMA buffers and interrupt/main stack are additional.
- Start with a provisional 20 KiB FreeRTOS heap only after checking the actual device RAM,
  link map and total static/dynamic budget. It is not a guaranteed fitting configuration.
- Allocation failure must abort startup; no scheduler start/retry after partial creation.
  The first adapter intentionally treats allocation failure as fatal and does not reclaim
  partial allocations; reset the MCU during development before another create attempt.
- Initial adapter requires a 1000 Hz kernel tick. The CubeIDE project supplies
  CMSIS-RTOS2 and FreeRTOS from the STM32 project sources.
- Before scheduler start: osKernelInitialize(), cuty_rtos_create(), cuty_rtos_start().
  Board initialization configures TIM4 but leaves PB6/PB7/PB8 low, compare at zero and
  PWM channels stopped. The physical-output compile gate remains disabled by default;
  this application does not bind output callbacks.

Communication owns the target producer; overwriting uses nonblocking Get + Put with a
single producer and a single consumer. The consumer processes at most eight state events
and one latest target per joint per poll. A sequence barrier drops goals received before the latest
state-change command. Events older than 100 ms are rejected; delayed heartbeat records
retain their receive timestamps. RX overflow/malformed lines set a fault flag.
The queue byte timestamp is assigned in the ISR hook, and a frame uses its LF timestamp.
Real DMA reception must carry equivalent timestamps, enforce fragment timeouts and
resynchronize after UART framing/overrun errors. The board's HAL RX error callback
aborts and rearms one-byte reception, and posts a fault to the safety owner.

Snapshots, reply queues and telemetry use timeout zero; congestion drops records.
The board TX task drains `cuty_take_reply` and `cuty_take_telemetry`, encodes V2
ACK/NACK/STATE/TELEM lines, and serializes HAL transmit calls. Malformed or overflow
frames generate `V2,NACK,FRAME,UNKNOWN`. Diagnostics counters
include RX fault notifications and reply/snapshot congestion; final TX-queue losses,
task runtimes and memory high-water marks still need instrumentation.

## Protocol V2 (implemented; still experimental)

Separate from the legacy SET_HEAD/SET_BODY design sketches in docs/protocol.
LF terminated, optional single CR before LF. Max 63 stored bytes, ASCII only;
embedded NUL, non-ASCII or oversized lines discard through LF. Empty lines are invalid.
No whitespace trimming, exponent/NaN/Infinity, plus sign, decimal point or extra fields.

| Record without LF | Meaning |
| --- | --- |
| V2,HB | Refresh heartbeat (does not recover a fault) |
| V2,INFO | Return the loaded profile ID without changing state or motion targets |
| V2,ARM | DISARMED → READY, only with fresh heartbeat |
| V2,START | READY → ACTIVE, only with fresh heartbeat |
| V2,DISARM | Inhibit output and discard movement; FAULT stays latched, other states → DISARMED |
| V2,RESET | FAULT → DISARMED; clears heartbeat validity |
| V2,TARGET,HEAD_PAN,350 | Joint HEAD_PAN, LEFT_ARM or RIGHT_ARM; signed integer -1000..1000 milli-units → -1..1 |

`V2,INFO` returns `V2,ACK,<sequence>,OK,<state>,sha256:<64 lowercase hex>` on a
physical profile build and `... ,none` on other builds. The integrated Raspberry
executor requires the SHA-256 value to match its loaded profile. This check does not
replace per-axis calibration or supervised physical validation.

Joints are named HEAD_PAN, LEFT_ARM and RIGHT_ARM. Coordinates are normalized to each calibrated axis range, not physical angles. No degree or raw PWM commands are accepted. The design maps J7–J9 to these axes; final continuity and servo mapping still require physical confirmation. V2 has no CRC/session handshake, replay protection or
link authentication; corrupted yet valid ASCII may pass parsing. A production protocol
must settle integrity, sessions, acknowledgements, error vocabulary and recovery.
The Raspberry bridge and STM32 USART2 RX/TX implementation communicate using V2 records. Connecting the bridge does not send ARM/START; the executor verifies DISARMED and requires an explicit action to activate. No compatibility with older command sketches is claimed.

## Motion and safety

The core starts DISARMED. HB → ARM → START is explicit. A goal in the wrong state,
nonfinite/out-of-range value, invalid command or excessive control dt faults an armed
controller. Heartbeat expiry at >=500 ms latches FAULT in the STM32 firmware.
HB alone never recovers; RESET, fresh HB, ARM and START are needed. DISARM is always
accepted and inhibits output intent, but cannot clear a latched fault. Wrap-safe unsigned elapsed arithmetic
is used; it assumes polling within the 32-bit millisecond wrap interval.

The initial filter applies a damped acceleration command in normalized units, clamps
acceleration and velocity and checks each predicted position against configured bounds.
It is not a calibrated robot trajectory planner, jerk-limited trajectory or IMU PID.
If bounds cannot be maintained the core faults rather than sending an out-of-range
position. Fault/disarm freeze the command immediately; normal trajectory acceleration
limits do not apply to that logical emergency stop. A physical servo may still move
toward its last commanded position: freezing a setpoint does not prove physical rest.

Fault policies in the portable controller are logical intents. The board output driver
rejects output without confirmed mechanical calibration and servo-to-joint mapping. The
default CubeIDE build leaves PWM callbacks unbound; a profile build binds them only
after validating all three axes. `CUTY_FREEZE_COMMAND`
can preserve torque at a stale position and must never be treated as a physically safe
failure mode:

- FREEZE_COMMAND retains the last commanded setpoint only if output was previously
  requested by ACTIVE (never energizes a READY or boot fault), useful where releasing torque
  could drop a load. It can still stall/heat a servo or trap a mechanism.
- RELEASE_OUTPUT requests no output, useful where continuing torque is dangerous.
  It can let a gravity-loaded joint fall.

Neither policy is certified safe for the assembled mechanism. There is no universal
90-degree safe position. Mechanical risk assessment, torque support, power removal and
operator recovery must determine the physical policy. Startup/reset never energizes a
joint. Normalized zero is the confirmed calibrated center in a profile build, not an
independent position measurement. The output driver additionally requires a valid
profile and explicit ARM/START; its `output_requested` flag alone is not an arming gate.

## Pins and board initialization

The carrier v1.1 netlist and schematic design specify:

| Function | Carrier mapping | MCU alternate function to verify for exact package |
| --- | --- | --- |
| Pi TX physical 8 → STM32 RX | PA3 / USART2_RX | AF7 |
| STM32 TX → Pi RX physical 10 | PA2 / USART2_TX | AF7 |
| Active PWM outputs | PB6/PB7/PB8 / TIM4 CH1–3 to J7/J8/J9 | AF2 |
| Reserved connectors | PB9/J10 and PA8/J11 | Not configured for servo output |

The repository names STM32F401CCU6 as the design target. Confirm the actual chip
marking and module revision before programming. The netlist records design intent;
final carrier continuity and soldering still require inspection.

USART2 is configured for 115200 baud, 8N1. The board code derives the TIM4 input
clock from PCLK1 and the APB1 prescaler rule for STM32F401, then computes PSC for a
1 MHz counter and ARR=19999 (50 Hz). It rejects clocks that cannot produce this exact
counter rate. The default firmware keeps PWM disabled; the profile build enables the
three outputs only after profile validation and explicit ARM/START. Before attaching
the assembled mechanism, measure the 50 Hz period and pulse widths on PB6/PB7/PB8 with
an oscilloscope.

The 20 ms controller update is separate from PWM generation: tick jitter affects
when the next setpoint is prepared, not pulse timing from a hardware timer. Measure
execution time, deadlines, phase/latch latency and missed updates under UART load.
The historical independent test ranges are 1000–2850 us, 1000–2700 us and
1000–2850 us, in test-servo order only. About 125 degrees of total travel was
reported during bench trials, but that does not define a safe range or center.
These ranges are pulse ceilings, not safe mechanism endpoints. Actual center, direction, deadband, velocity,
acceleration, current limits and mapping require joint-by-joint bench calibration.

Keep the dedicated servo supply; verify current capacity, fusing, polarity, noise and
ground references. The carrier separates PGND/GND and joins at NT1; validate that
design electrically rather than introducing an unintended second high-current return.
No changes to Raspberry GPIO, overlays, display, ReSpeaker or drivers are required here.

## Build and tests

Portable core, GCC/Clang-compatible C11 compiler on PATH:

    python stm32/tests/run_host_tests.py

Windows PowerShell with a portable Zig C compiler, if installed:

    $env:CC = 'C:/path/to/zig.exe cc'
    python stm32/tests/run_host_tests.py

These compile/run native host C tests: partial CRLF frames, invalid grammar,
oversized/NUL input and recovery, latest setpoint, velocity/acceleration and bounds,
state transitions, heartbeat loss and tick rollover, fault recovery and pulse conversion.
A second executable compiles the actual motion_tasks.c adapter against minimal CMSIS
test doubles and checks mailbox replacement, state-command barriers, stale goals, reply
queues, copied snapshots and RX overflow. This is sequential control-flow testing, not
a preemptive scheduler, genuine CMSIS kernel, IRQ/DMA, HAL or Black Pill validation.
It does not prove interleavings, task timing or driver integration.

To repeat ARM application-object compilation with a real compiler and CMSIS headers:

    python stm32/tests/compile_arm_objects.py --cc C:/path/to/arm-none-eabi-gcc.exe --cmsis C:/path/to/CMSIS/RTOS2/Include

On 2026-11-17 the five application translation units, including the adapter, compiled
with the installed STM32CubeIDE GNU Tools for STM32 14.3.1 for Cortex-M4, with
-Wall -Wextra -Werror -pedantic. The generic cmsis_os2.h came from the installed
STM32Cube_FW_H7_V1.13.0 package; no H7 HAL, startup or board configuration was used.
That checks C/API declarations only: no FreeRTOS library or F401 image was linked.
Native tests ran with TinyCC 0.9.27 i386 on Windows; that compiler lives only in ignored
.local-tools/cuty-tcc32/tcc/tcc.exe. GCC/Clang is the recommended normal host test setup.

Web:

    cd web
    npm run build
    npm run lint
    npm test
    npm run test:e2e

If port 5173 is occupied, PowerShell: $env:CUTY_TEST_PORT='5187' before the e2e command.

The new component tests cover local stage progression/fault/reset, bilingual text and
reduced motion. Browser checks cover the existing scene/expression/PCB/wiring flows
plus the new section across desktop/tablet/mobile.
All styles are scoped to .motion-control. The section is appended after the existing
outro to preserve the existing chapter positions/3D shot order; the only navigation
addition uses the current link style. No existing global palette, font, shot, animation,
PCB or wiring component is restyled.

## Remaining physical verification

1. Confirm the exact STM32F401CCU6 board revision, power arrangement, pin continuity
   and the fixed PB6/PB7/PB8 to J7/J8/J9 carrier mapping.
2. Complete supervised per-axis center, direction and safe-range calibration. The
   observed 125° sweep and historical pulse ranges are not safety limits.
3. Compile and flash the manual-calibration firmware first. Only after reviewing and
   explicitly confirming the three measured axes should the profile build be generated.
4. Verify the already-built profile firmware with the 19-stage sequence in
   [`robot-validation.md`](robot-validation.md): isolated axes, coordinated motion,
   head following, voice, UART loss, stop, restart, power and temperature.
5. The profile-gated build uses explicit ARM/START; the default build keeps PWM
   disabled. Host tests and successful UART ACKs do not certify servo output or
   mechanical release behavior. PWM disable is not an electrical power cutoff.

## Primary references

- [ST STM32F401CC product and datasheet downloads](https://www.st.com/en/microcontrollers-microprocessors/stm32f401cc.html)
- [ST RM0368 reference manual](https://www.st.com/resource/en/reference_manual/rm0368-stm32f401xbc-and-stm32f401xde-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
- [ARM CMSIS-RTOS2 usage and ISR API restrictions](https://arm-software.github.io/CMSIS_6/latest/RTOS2/usingOS2.html)
- [ARM CMSIS-RTOS2 threads, priorities and stack bytes](https://arm-software.github.io/CMSIS_6/latest/RTOS2/group__CMSIS__RTOS__ThreadMgmt.html)
- [ARM CMSIS-FreeRTOS wrapper limitations](https://arm-software.github.io/CMSIS-FreeRTOS/v10.5.1/tech_data.html)

## File inventory for this addition

New files:

- web/src/components/MotionControl.tsx — local interactive section.
- web/src/components/motion-control.css — styles scoped to the new section.
- web/src/data/motionControl.ts — bilingual tasks and illustrative stages.
- web/src/components/MotionControl.test.tsx — component behavior tests.
- web/e2e/motion-control.spec.ts — desktop/tablet/mobile checks.
- stm32/App/rtos/motion_tasks.c and motion_tasks.h — dry-run CMSIS adapter.
- stm32/tests/test_motion.c — portable logic tests.
- stm32/tests/run_host_tests.py and compile_arm_objects.py — native execution (host compiler required) and ARM object build helpers.
- stm32/App/control/fir_filter.c/.h — fixed-buffer FIR used only for HEAD_PAN.
- raspberry/src/cuty/audio/speech_bandpass.py — optional PCM16 input filter, disabled by default.
- raspberry/tests/test_speech_bandpass.py — host signal, format, and continuity tests.
- web/src/components/DigitalSignalProcessing.tsx — bilingual, local calculation and plots.
- web/e2e/digital-signal-processing.spec.ts — desktop/tablet/mobile coverage.
- docs/digital-signal-processing-fir.md — DSP math, audio implementation, and A/B procedure.
- stm32/tests/test_rtos.c and fakes/cmsis_os2.h — adapter tests with test doubles.
- stm32/tests/run_host_tests.py — native compile/run entry point.
- stm32/tests/compile_arm_objects.py — real ARM object-compilation entry point.
- docs/freertos-motion-control.md — this architecture, status and bring-up guide.

Reused the existing UART, body_control, safety and servo C/H files and the IMU header.
Updated their README files, STM32/body-control/protocol/head-follow/roadmap documentation.
App.tsx mounts the motion and DSP sections and integrates their navigation links.
The DSP section uses scoped styles and local synthetic signals. No physical UART/PWM,
servo output, PCB, wiring, model geometry, or Raspberry device/driver configuration
was changed. The Raspberry change is limited to the optional microphone-input
processor before provider send; the existing camera, playback, and music paths remain
separate. Playwright can select a different port via CUTY_TEST_PORT.

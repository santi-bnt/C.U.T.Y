# Current configuration update

Three planned joints: HEAD_PAN (J7), LEFT_ARM (J8), RIGHT_ARM (J9). J10 and J11 are reserved. Experimental protocol V2 accepts named joints only; V1 frames and reserved axes are rejected. The controller remains dry-run. References below to a single target mailbox or five axes are historical and superseded by three independent one-entry mailboxes.

# FreeRTOS / Motion Control — initial, dry-run only

## Actual implementation boundary

The portable C modules implement byte-stream framing, strict experimental command parsing,
three normalized commanded setpoints, a damped trajectory filter, position/velocity/acceleration
limits, heartbeat checks, a latched safety state machine, and a pure pulse-width conversion.
They do not initialize pins, start timers, transmit UART, read sensors, or move a servo.
The CMSIS-RTOS2 adapter is initial integration source, not a validated STM32 firmware image.
There is no CubeMX project, HAL, linker/startup configuration, or on-board test result.
IMU is an interface declaration; PID remains a placeholder.

The interactive website is a scripted educational visualization. Its PAN +0.35 example,
slowed stages and 500 ms fault scenario are illustrative, not live telemetry or a firmware
emulator. It has no serial, Bluetooth, WebSocket, HTTP command or robot-control transport.
Raspberry head_follow.py remains dry-run; no Raspberry configuration or drivers were changed.

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
- Initial adapter requires a 1000 Hz kernel tick and accepts only CUTY_RTOS_DRY_RUN=1.
  Supply CMSIS-RTOS2 headers/library through a compatible STM32Cube FreeRTOS integration.
- Before scheduler start: osKernelInitialize(), cuty_rtos_create(), cuty_rtos_start().
  Board initialization must leave actuator outputs disabled; no PWM callbacks are provided.

Communication owns the target producer; overwriting uses nonblocking Get + Put with a
single producer and a single consumer. The consumer processes at most eight state events
and one latest target per joint per poll. A sequence barrier drops goals received before the latest
state-change command. Events older than 100 ms are rejected; delayed heartbeat records
retain their receive timestamps. RX overflow/malformed lines set a fault flag.
The queue byte timestamp is assigned in the ISR hook, and a frame uses its LF timestamp.
Real DMA reception must carry equivalent timestamps, enforce fragment timeouts and
resynchronize after UART framing/overrun errors. That adapter is not implemented.

Snapshots, reply queues and telemetry use timeout zero; congestion drops records.
The future UART TX owner can drain cuty_take_reply and cuty_take_telemetry, but no wire
encoding or HAL transmit driver is supplied. Replies to malformed/overflow input are
currently fault counters/flags, not per-frame UART ERR records. Diagnostics counters
include RX fault notifications and reply/snapshot congestion; final TX-queue losses,
task runtimes and memory high-water marks still need instrumentation.

## Experimental protocol V2 (host/dry-run only)

Separate from the legacy SET_HEAD/SET_BODY design sketches in docs/protocol.
LF terminated, optional single CR before LF. Max 63 stored bytes, ASCII only;
embedded NUL, non-ASCII or oversized lines discard through LF. Empty lines are invalid.
No whitespace trimming, exponent/NaN/Infinity, plus sign, decimal point or extra fields.

| Record without LF | Meaning |
| --- | --- |
| V2,HB | Refresh heartbeat (does not recover a fault) |
| V2,ARM | DISARMED → READY, only with fresh heartbeat |
| V2,START | READY → ACTIVE, only with fresh heartbeat |
| V2,DISARM | Inhibit output and discard movement; FAULT stays latched, other states → DISARMED |
| V2,RESET | FAULT → DISARMED; clears heartbeat validity |
| V2,TARGET,HEAD_PAN,350 | Joint HEAD_PAN, LEFT_ARM or RIGHT_ARM; signed integer -1000..1000 milli-units → -1..1 |

Joints are named HEAD_PAN, LEFT_ARM and RIGHT_ARM. Their coordinates remain abstract simulation units, not calibrated physical angles. No degree or PWM commands are accepted. The proposed J7–J9 assignments remain physically unverified. The V2 sketch has no CRC/session handshake, replay protection or
link authentication; corrupted yet valid ASCII may pass parsing. A production protocol
must settle integrity, sessions, acknowledgements, error vocabulary and recovery.
No Raspberry adapter is enabled and no compatibility with older command sketches is claimed.

## Motion and safety

The core starts DISARMED. HB → ARM → START is explicit. A goal in the wrong state,
nonfinite/out-of-range value, invalid command or excessive control dt faults an armed
controller. Heartbeat expiry at >=500 ms in the dry-run profile latches FAULT.
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

Fault policies are logical intents only:

- FREEZE_COMMAND retains the last commanded setpoint only if output was previously
  requested by ACTIVE (never energizes a READY or boot fault), useful where releasing torque
  could drop a load. It can still stall/heat a servo or trap a mechanism.
- RELEASE_OUTPUT requests no output, useful where continuing torque is dangerous.
  It can let a gravity-loaded joint fall.

Neither policy is approved for the real mechanism. There is no universal 90-degree
safe position. Mechanical risk assessment, torque support, power removal and operator
recovery must determine the physical policy. Startup/reset must never energize an
uncalibrated joint; normalized zero is an abstract test initial condition, not physical
neutral. Before adding PWM, require verified initial pose/calibration and a hardware
arming gate; the core's output_requested function is not such a gate.

## Pins, timers and configuration proposal (not generated initialization)

The carrier v1.1 netlist and schematic design specify:

| Function | Carrier mapping | MCU alternate function to verify for exact package |
| --- | --- | --- |
| Pi TX physical 8 → STM32 RX | PA3 / USART2_RX | AF7 |
| STM32 TX → Pi RX physical 10 | PA2 / USART2_TX | AF7 |
| PWM outputs 1–4 | PB6/PB7/PB8/PB9 / TIM4 CH1–4 | AF2 |
| PWM output 5 | PA8 / TIM1 CH1 | AF1 |

The repository names STM32F401CCU6 as the design target. The actual chip marking,
board revision, package, oscillator and memory have not been observed/verified.
The netlist confirms design intent, not physical continuity or soldering.
Consult the exact part's ST datasheet AF tables before generating code.

Initial proposal: 115200 baud, 8N1; hardware PWM period 20 ms (50 Hz), 1 us counter
resolution. Compute each timer clock from the verified RCC/APB/TIMPRE configuration,
then PSC = timer_clock / 1 MHz - 1 and ARR = 19999 only when division is exact.
For an illustrative timer input of 84 MHz, PSC would be 83. This is NOT a measured
clock or a generated board configuration. TIM1 is on APB2 and TIM4 on APB1; do not
assume their input clocks match PCLK. Respect the TIMPRE/APB rules in RM0368.
Use CCR preload/latching, configure TIM1 output enable correctly, and verify both
timers with an oscilloscope before connecting servos.

The 20 ms controller update is separate from PWM generation: tick jitter affects
when the next setpoint is prepared, not pulse timing from a hardware timer. Measure
execution time, deadlines, phase/latch latency and missed updates under UART load.
Actual servo pulse endpoints, direction, deadband, velocity, acceleration and current
limits require joint-by-joint bench calibration. Never use example 1000–2000 us from
unit tests as mechanically verified endpoints.

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

## Bringing this to an actual STM32

1. Record chip marking, exact Black Pill revision, oscillator and power arrangement.
   Confirm RAM/flash, package AF tables and the carrier schematic/physical pin continuity.
2. Agree servo/joint mapping, sign, calibration, mechanical limits and risk-specific fault
   policy. Define safe initial-pose acquisition and explicit physical arming.
3. Generate a fresh CubeMX/STM32CubeIDE project for that exact MCU with compatible
   FreeRTOS + CMSIS-RTOS2; set clocks/tick, NVIC syscall priorities, USART2 IRQ or DMA,
   TIM4/TIM1, timer preloads and disabled initial output. Reserve HAL timebase separately
   if needed. Version the .ioc and generated build configuration.
4. Add portable modules and adapter with CUTY_RTOS_DRY_RUN=1 first. Build with the real
   ARM toolchain and inspect link map, stack/heap and RTOS API compatibility. Do not
   remove the dry-run guard until independent physical safety integration exists.
5. Add bounded IRQ/DMA driver/resynchronization, validated TX protocol and a task-liveness
   watchdog. Confirm timing with stress traffic, queue overflow, scheduler overruns,
   power interruptions, boot/reset and heartbeat loss while outputs are disconnected.
6. Measure PWM on a scope first; then one supported/unloaded joint with current-limited
   supply and physical stop, then mechanical integration. Record actual results.
   Only then design the opt-in Raspberry adapter; keep existing head follow in dry-run.

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
- stm32/tests/test_rtos.c and fakes/cmsis_os2.h — adapter tests with test doubles.
- stm32/tests/run_host_tests.py — native compile/run entry point.
- stm32/tests/compile_arm_objects.py — real ARM object-compilation entry point.
- docs/freertos-motion-control.md — this architecture, status and bring-up guide.

Reused the existing UART, body_control, safety and servo C/H files and the IMU header.
Updated their README files, STM32/body-control/protocol/head-follow/roadmap documentation.
App.tsx mounts the new section and integrates its navigation link, active state and
existing header tone. The existing controller summary changes only its implementation
status sentence; its test assertion follows that sentence. Existing browser tests
expect the one added link; Playwright can select a different port via CUTY_TEST_PORT.
No existing viewer, expression, PCB, wiring, global style or Raspberry/hardware file changed.

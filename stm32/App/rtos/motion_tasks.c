/* CMSIS-RTOS2 adapter: the task/queue topology of the C.U.T.Y STM32 firmware.
 * Hardware is reached only through App/board/cuty_board.h, so the same file
 * runs on the Black Pill, in the FreeRTOS POSIX simulator and in host tests.
 *
 *   USART2 IRQ --rx queue--> CommunicationTask --commands/targets--> ServoControlTask
 *   ServoControlTask --replies/snapshots--> DiagnosticsTask/TxTask --> USART2 TX
 *   SafetyTask: liveness of ServoControlTask, IWDG refresh, battery, kill switch
 *
 * CUTY_RTOS_DRY_RUN=1 runs everything but never enables the PWM pins. */
#include "motion_tasks.h"
#include "../board/cuty_board.h"
#include "../communication/wire.h"
#include "../power/battery.h"
#include "../servos/calibration.h"
#include "../supervision/liveness.h"
#include "cmsis_os2.h"
#include <string.h>
#if !defined(CUTY_RTOS_DRY_RUN) || (CUTY_RTOS_DRY_RUN != 0 && CUTY_RTOS_DRY_RUN != 1)
#error "Define CUTY_RTOS_DRY_RUN=1 (PWM pins never enabled) or 0 (PWM build)."
#endif

/* ServoControlTask thread flags */
#define INVALID_RX  1U
#define SUPERVISE   2U
#define BATTERY_LOW 4U
#define BATTERY_OK  8U
/* RxByte.flags */
#define RX_LOST_BEFORE 1U /* bytes were dropped (queue full) right before this one */
#define RX_UART_ERROR  2U /* framing/noise/overrun marker, carries no data */

#define CUTY_FRESH_MS         100U /* frames older than this when applied are stale */
#define CUTY_FRAGMENT_GAP_MS   50U /* silence inside a line discards the partial line */
#define CUTY_CONTROL_PERIOD_MS 10U
#define CUTY_STEP_MS           20U
#define CUTY_TELEMETRY_MS     200U
#define CUTY_DIAG_MS         5000U
#define CUTY_TX_PERIOD_MS       5U
/* Arms hang down at rest and the pan axis carries no gravity load, so on a
 * fault the servos are released (no pulses) rather than held. */
#define CUTY_LOSS_POLICY CUTY_RELEASE_OUTPUT

typedef struct { CutyCommand command; uint32_t received_ms, sequence; } Envelope;
typedef struct { uint8_t byte, flags; uint32_t received_ms; } RxByte;
static osMessageQueueId_t rx, commands, targets[CUTY_AXES], snapshots, replies, telemetry, diags;
static osThreadId_t communication, servo, safety, diagnostics, tx;
static CutyController controller;
static bool created;
static volatile bool rx_lost;
static volatile uint32_t servo_beat_ms, battery_mv, rx_overflows, tx_overflows;
static const CutyServoCalibration calibration[CUTY_AXES] = CUTY_SERVO_CALIBRATION_DEFAULT;

/* At the required 1 kHz kernel tick, timestamps are milliseconds. */
bool cuty_uart_rx_isr(uint8_t byte) {
    if (!created) return false;
    RxByte item = {byte, rx_lost ? RX_LOST_BEFORE : 0U, osKernelGetTickCount()};
    if (osMessageQueuePut(rx, &item, 0, 0) == osOK) { rx_lost = false; return true; }
    rx_lost = true; ++rx_overflows;
    osThreadFlagsSet(servo, INVALID_RX); return false;
}
void cuty_uart_rx_error_isr(void) {
    if (!created) return;
    RxByte item = {0U, RX_UART_ERROR, osKernelGetTickCount()};
    if (osMessageQueuePut(rx, &item, 0, 0) == osOK) rx_lost = false;
    else { rx_lost = true; ++rx_overflows; osThreadFlagsSet(servo, INVALID_RX); }
}
bool cuty_take_reply(CutyReply *reply) { return created && osMessageQueueGet(replies, reply, 0, 0) == osOK; }
bool cuty_take_telemetry(CutySnapshot *s) { return created && osMessageQueueGet(telemetry, s, 0, 0) == osOK; }

static void drop_line(CutyParser *p) { p->used = 0; p->dropping = true; }

static void communication_task(void *unused) {
    (void)unused; CutyParser parser = {0}; uint32_t sequence = 0, last_byte_ms = 0;
    for (;;) {
        RxByte item;
        if (osMessageQueueGet(rx, &item, 0, osWaitForever) != osOK) continue;
        for (unsigned batch=0; batch<64; ++batch) {
            if (item.flags & (RX_LOST_BEFORE|RX_UART_ERROR)) {
                /* The line in progress lost bytes: discard it through the next LF. */
                drop_line(&parser); osThreadFlagsSet(servo, INVALID_RX);
            }
            if (!(item.flags & RX_UART_ERROR)) {
                if ((parser.used || parser.dropping) &&
                    (uint32_t)(item.received_ms - last_byte_ms) > CUTY_FRAGMENT_GAP_MS) {
                    /* Old fragment: never splice it onto newer bytes. */
                    parser.used = 0; parser.dropping = false; osThreadFlagsSet(servo, INVALID_RX);
                }
                last_byte_ms = item.received_ms;
                Envelope e = {0};
                CutyRxResult result = cuty_rx_byte(&parser, item.byte, &e.command);
                if (result == CUTY_RX_ERROR) osThreadFlagsSet(servo, INVALID_RX);
                if (result == CUTY_RX_COMMAND) {
                    e.received_ms=item.received_ms; e.sequence=++sequence;
                    osStatus_t status;
                    if (e.command.kind == CUTY_TARGET) {
                        Envelope old;
                        /* One producer; consumer may empty it between Get and Put. */
                        osMessageQueueGet(targets[e.command.axis],&old,0,0);
                        status=osMessageQueuePut(targets[e.command.axis],&e,0,0);
                    } else status=osMessageQueuePut(commands,&e,0,0);
                    if (status != osOK) osThreadFlagsSet(servo,INVALID_RX);
                }
            }
            if (batch==63 || osMessageQueueGet(rx,&item,0,0)!=osOK) break;
        }
        /* Yield to other work under continuous/noisy UART input. */
        osDelay(1);
    }
}

static void apply_outputs(void) {
    float x[CUTY_AXES]; uint16_t pulses[CUTY_AXES] = {1500U, 1500U, 1500U};
    for (unsigned i=0; i<CUTY_AXES; ++i) x[i]=controller.axes[i].commanded;
    bool enable = cuty_control_output_requested(&controller) &&
        (controller.safety.state==CUTY_ACTIVE || controller.safety.state==CUTY_FAULT);
    if (!cuty_servo_pulses(x, calibration, pulses)) {
        cuty_control_fault(&controller, CUTY_FAULT_LIMIT); enable = false;
    }
#if CUTY_RTOS_DRY_RUN
    enable = false;
#endif
    cuty_board_set_outputs(pulses, enable);
}

static void reply(uint32_t sequence, bool accepted, const CutyCommand *c, uint32_t *dropped_tx) {
    CutyReply r={sequence,accepted,c->kind,c->axis};
    if (osMessageQueuePut(replies,&r,0,0)!=osOK) ++*dropped_tx;
}

static void servo_task(void *unused) {
    (void)unused;
    uint32_t deadline=osKernelGetTickCount(), last_step=deadline, barrier=0, dropped_tx=0, rx_errors=0;
    for (;;) {
        uint32_t now=osKernelGetTickCount();
        servo_beat_ms=now; /* liveness beat read by SafetyTask */
        uint32_t flags=osThreadFlagsClear(INVALID_RX|SUPERVISE|BATTERY_LOW|BATTERY_OK);
        if (!(flags & osFlagsError)) {
            if (flags & INVALID_RX) {
                ++controller.safety.invalid_commands; ++rx_errors;
                cuty_control_fault(&controller, CUTY_FAULT_RX_ERROR);
            }
            if (flags & BATTERY_LOW) cuty_control_set_inhibit(&controller, true);
            if (flags & BATTERY_OK) cuty_control_set_inhibit(&controller, false);
        }
        Envelope e;
        for (unsigned n=0; n<8 && osMessageQueueGet(commands,&e,0,0)==osOK; ++n) {
            bool fresh=(uint32_t)(now-e.received_ms)<=CUTY_FRESH_MS;
            bool accepted=false;
            if (fresh) accepted=cuty_control_command(&controller,&e.command,e.received_ms);
            else { ++controller.safety.invalid_commands; cuty_control_fault(&controller, CUTY_FAULT_STALE_COMMAND); }
            /* Targets received before a state-changing command are obsolete. */
            if (e.command.kind!=CUTY_HEARTBEAT) barrier=e.sequence;
            reply(e.sequence,accepted,&e.command,&dropped_tx);
        }
        cuty_safety_check(&controller.safety,now);
        for (unsigned axis=0; axis<CUTY_AXES; ++axis) {
          if (osMessageQueueGet(targets[axis],&e,0,0)==osOK) {
            bool newer=(int32_t)(e.sequence-barrier)>0;
            bool accepted=newer && (uint32_t)(now-e.received_ms)<=CUTY_FRESH_MS &&
                cuty_control_command(&controller,&e.command,now);
            reply(e.sequence,accepted,&e.command,&dropped_tx);
          }
        }
        uint32_t elapsed=now-last_step;
        if (elapsed>=CUTY_STEP_MS) {
            cuty_control_tick(&controller,now,elapsed/1000.0f); last_step=now;
            apply_outputs();
            /* Latest-value mailbox: replace an unread snapshot, never count it as a loss. */
            static CutySnapshot snapshot, stale;
            snapshot=(CutySnapshot){now,rx_errors,dropped_tx,controller,battery_mv,cuty_board_outputs_enabled()};
            osMessageQueueGet(snapshots,&stale,0,0);
            if (osMessageQueuePut(snapshots,&snapshot,0,0)!=osOK) ++dropped_tx;
        } else if (controller.safety.state!=CUTY_ACTIVE) {
            cuty_control_tick(&controller,now,0.02f); /* freeze immediately */
            apply_outputs(); /* release within one 10 ms poll */
        }
        deadline+=CUTY_CONTROL_PERIOD_MS;
        if ((int32_t)(deadline-osKernelGetTickCount())<=0) {
            ++controller.safety.invalid_commands; cuty_control_fault(&controller, CUTY_FAULT_CONTROL_OVERRUN);
            deadline=osKernelGetTickCount()+CUTY_CONTROL_PERIOD_MS;
        }
        osDelayUntil(deadline);
    }
}

/* Independent of the control owner: if ServoControlTask stops beating, kill
 * the PWM in hardware and stop feeding the IWDG so the MCU resets. */
static void safety_task(void *unused) {
    (void)unused; uint32_t deadline=osKernelGetTickCount(); unsigned divider=0;
    CutyLiveness liveness; cuty_liveness_init(&liveness, CUTY_LIVENESS_TIMEOUT_MS);
    CutyBattery battery; cuty_battery_init(&battery);
    for (;;) {
        uint32_t now=osKernelGetTickCount();
        osThreadFlagsSet(servo,SUPERVISE);
        if (cuty_liveness_check(&liveness, servo_beat_ms, now)) cuty_board_watchdog_kick();
        else cuty_board_kill_outputs();
        if (++divider >= 10U) { /* 10 Hz battery supervision */
            divider = 0;
            CutyBatteryEvent event = cuty_battery_update(&battery, cuty_board_battery_mv(), now);
            battery_mv = battery.level == CUTY_BATTERY_ABSENT ? 0U : battery.filtered_mv;
            if (event == CUTY_BATTERY_BECAME_CRITICAL) osThreadFlagsSet(servo, BATTERY_LOW);
            if (event == CUTY_BATTERY_RECOVERED) osThreadFlagsSet(servo, BATTERY_OK);
        }
        deadline+=CUTY_CONTROL_PERIOD_MS;
        if ((int32_t)(deadline-osKernelGetTickCount())<=0) deadline=osKernelGetTickCount()+CUTY_CONTROL_PERIOD_MS;
        osDelayUntil(deadline);
    }
}

/* PC13 LED: DISARMED short blink each second, READY slow blink, ACTIVE on, FAULT fast blink. */
static void show_state(CutyState state, unsigned tick) {
    bool on;
    switch (state) {
    case CUTY_ACTIVE: on = true; break;
    case CUTY_READY: on = (tick / 2U) % 2U == 0U; break;
    case CUTY_FAULT: on = tick % 2U == 0U; break;
    default: on = tick % 5U == 0U; break;
    }
    cuty_board_led(on);
}

static void diagnostics_task(void *unused) {
    (void)unused; uint32_t last_diag=osKernelGetTickCount(), deadline=last_diag; unsigned tick=0;
    CutyState state=CUTY_DISARMED;
    for (;;) {
        CutySnapshot snapshot;
        if (osMessageQueueGet(snapshots,&snapshot,0,0)==osOK) {
            state=snapshot.controller.safety.state;
            osMessageQueuePut(telemetry,&snapshot,0,0); /* drop, never block control */
        }
        show_state(state, ++tick);
        uint32_t now=osKernelGetTickCount();
        if ((uint32_t)(now-last_diag) >= CUTY_DIAG_MS) {
            last_diag=now;
            osThreadId_t ids[CUTY_DIAG_TASKS]={communication,servo,safety,diagnostics,tx};
            CutyWireDiag d={now,{0},cuty_board_heap_min_free(),rx_overflows,tx_overflows};
            for (unsigned i=0;i<CUTY_DIAG_TASKS;++i) d.stack_free_bytes[i]=osThreadGetStackSpace(ids[i]);
            osMessageQueuePut(diags,&d,0,0);
        }
        deadline+=CUTY_TELEMETRY_MS; /* fixed 5 Hz period, no drift */
        if ((int32_t)(deadline-osKernelGetTickCount())<=0) deadline=osKernelGetTickCount()+CUTY_TELEMETRY_MS;
        osDelayUntil(deadline);
    }
}

static void send_line(const char *line, size_t length) {
    if (!length) return;
    if (cuty_board_uart_tx_free() < length) { ++tx_overflows; return; } /* whole lines only */
    cuty_board_uart_write(line, length);
}

/* Sole owner of USART2 TX: boot record, ACK/NAK, telemetry and diagnostics. */
static void tx_task(void *unused) {
    (void)unused; char line[CUTY_WIRE_LINE_MAX];
    CutyWireBoot boot; cuty_board_info(&boot);
    send_line(line, cuty_wire_boot(line, sizeof line, &boot));
    for (;;) {
        CutyReply r;
        while (cuty_take_reply(&r)) {
            CutyWireReply w={r.sequence,r.accepted,r.kind,r.axis};
            send_line(line, cuty_wire_reply(line, sizeof line, &w));
        }
        CutySnapshot s;
        if (cuty_take_telemetry(&s)) {
            CutyWireTelemetry t={s.timestamp_ms,s.controller.safety.state,s.controller.safety.fault_reason,
                s.output_enabled,{0},s.battery_mv,s.rx_errors,s.dropped_tx+tx_overflows};
            for (unsigned i=0;i<CUTY_AXES;++i) t.commanded_milli[i]=cuty_wire_milli(s.controller.axes[i].commanded);
            send_line(line, cuty_wire_telemetry(line, sizeof line, &t));
        }
        CutyWireDiag d;
        if (osMessageQueueGet(diags,&d,0,0)==osOK) send_line(line, cuty_wire_diag(line, sizeof line, &d));
        osDelay(CUTY_TX_PERIOD_MS);
    }
}

bool cuty_rtos_create(void) {
    if (created || osKernelGetState()!=osKernelReady || osKernelGetTickFreq()!=1000) return false;
    CutyLimits limits[CUTY_AXES];
    for (unsigned i=0;i<CUTY_AXES;++i) limits[i]=(CutyLimits){-1,1,0.8f,1.5f};
    if (!cuty_control_init(&controller,limits,500,CUTY_LOSS_POLICY)) return false;
    rx=osMessageQueueNew(256,sizeof(RxByte),0);
    commands=osMessageQueueNew(8,sizeof(Envelope),0);
    for (unsigned axis=0; axis<CUTY_AXES; ++axis) {
        targets[axis]=osMessageQueueNew(1,sizeof(Envelope),0);
        if (!targets[axis]) return false;
    }
    snapshots=osMessageQueueNew(1,sizeof(CutySnapshot),0);
    replies=osMessageQueueNew(8,sizeof(CutyReply),0);
    telemetry=osMessageQueueNew(1,sizeof(CutySnapshot),0);
    diags=osMessageQueueNew(1,sizeof(CutyWireDiag),0);
    if (!rx||!commands||!snapshots||!replies||!telemetry||!diags) return false;
    const osThreadAttr_t ca={.name="CommunicationTask",.stack_size=1536,.priority=osPriorityAboveNormal};
    const osThreadAttr_t va={.name="ServoControlTask",.stack_size=1536,.priority=osPriorityHigh};
    const osThreadAttr_t sa={.name="SafetyTask",.stack_size=1024,.priority=osPriorityHigh1};
    const osThreadAttr_t da={.name="DiagnosticsTask",.stack_size=1024,.priority=osPriorityLow};
    const osThreadAttr_t ta={.name="TxTask",.stack_size=1536,.priority=osPriorityNormal};
    communication=osThreadNew(communication_task,0,&ca);
    servo=osThreadNew(servo_task,0,&va);
    safety=osThreadNew(safety_task,0,&sa);
    diagnostics=osThreadNew(diagnostics_task,0,&da);
    tx=osThreadNew(tx_task,0,&ta);
    created=communication&&servo&&safety&&diagnostics&&tx;
    /* Any failure is fatal to startup; do not start kernel or retry creation. */
    return created;
}
bool cuty_rtos_start(void) { return created && osKernelStart()==osOK; }

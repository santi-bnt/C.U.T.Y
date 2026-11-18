/* Experimental CMSIS-RTOS2 adapter. Not linked to HAL or physical PWM. */
#include "motion_tasks.h"
#include "cmsis_os2.h"
#include <string.h>
#if !defined(CUTY_RTOS_DRY_RUN) || CUTY_RTOS_DRY_RUN != 1
#error "Only CUTY_RTOS_DRY_RUN=1 is supported; physical integration is blocked."
#endif
#define INVALID_RX 1U
#define SUPERVISE 2U
typedef struct { CutyCommand command; uint32_t received_ms, sequence; } Envelope;
typedef struct { uint8_t byte; uint32_t received_ms; } RxByte;
static osMessageQueueId_t rx, commands, targets, snapshots, replies, telemetry;
static osThreadId_t communication, servo, safety, diagnostics;
static CutyController controller;
static bool created;
/* At the required 1 kHz kernel tick, timestamps are milliseconds. */
bool cuty_uart_rx_isr(uint8_t byte) {
    if (!created) return false;
    RxByte item = {byte, osKernelGetTickCount()};
    if (osMessageQueuePut(rx, &item, 0, 0) == osOK) return true;
    osThreadFlagsSet(servo, INVALID_RX); return false;
}
bool cuty_take_reply(CutyReply *reply) { return created && osMessageQueueGet(replies, reply, 0, 0) == osOK; }
bool cuty_take_telemetry(CutySnapshot *s) { return created && osMessageQueueGet(telemetry, s, 0, 0) == osOK; }
static void communication_task(void *unused) {
    (void)unused; CutyParser parser = {0}; uint32_t sequence = 0;
    for (;;) {
        RxByte item;
        if (osMessageQueueGet(rx, &item, 0, osWaitForever) != osOK) continue;
        for (unsigned batch=0; batch<64; ++batch) {
            Envelope e = {0};
            CutyRxResult result = cuty_rx_byte(&parser, item.byte, &e.command);
            if (result == CUTY_RX_ERROR) osThreadFlagsSet(servo, INVALID_RX);
            if (result == CUTY_RX_COMMAND) {
                e.received_ms=item.received_ms; e.sequence=++sequence;
                osStatus_t status;
                if (e.command.kind == CUTY_TARGET) {
                    Envelope old;
                    /* One producer; consumer may empty it between Get and Put. */
                    osMessageQueueGet(targets,&old,0,0);
                    status=osMessageQueuePut(targets,&e,0,0);
                } else status=osMessageQueuePut(commands,&e,0,0);
                if (status != osOK) osThreadFlagsSet(servo,INVALID_RX);
            }
            if (batch==63 || osMessageQueueGet(rx,&item,0,0)!=osOK) break;
        }
        /* Yield to other work under continuous/noisy UART input. */
        osDelay(1);
    }
}
static void servo_task(void *unused) {
    (void)unused;
    uint32_t deadline=osKernelGetTickCount(), last_step=deadline, barrier=0, dropped_tx=0, rx_errors=0;
    for (;;) {
        uint32_t now=osKernelGetTickCount();
        uint32_t flags=osThreadFlagsClear(INVALID_RX|SUPERVISE);
        if (!(flags & osFlagsError) && (flags & INVALID_RX)) { cuty_control_invalid(&controller); ++rx_errors; }
        Envelope e;
        for (unsigned n=0; n<8 && osMessageQueueGet(commands,&e,0,0)==osOK; ++n) {
            bool fresh=(uint32_t)(now-e.received_ms)<=100;
            bool accepted=false;
            if (fresh) accepted=cuty_control_command(&controller,&e.command,e.received_ms);
            else cuty_control_invalid(&controller);
            /* Targets received before a state-changing command are obsolete. */
            if (e.command.kind!=CUTY_HEARTBEAT) barrier=e.sequence;
            CutyReply reply={e.sequence,accepted};
            if (osMessageQueuePut(replies,&reply,0,0)!=osOK) ++dropped_tx;
        }
        cuty_safety_check(&controller.safety,now);
        if (osMessageQueueGet(targets,&e,0,0)==osOK) {
            bool newer=(int32_t)(e.sequence-barrier)>0;
            bool accepted=newer && (uint32_t)(now-e.received_ms)<=100 &&
                cuty_control_command(&controller,&e.command,now);
            CutyReply reply={e.sequence,accepted};
            if (osMessageQueuePut(replies,&reply,0,0)!=osOK) ++dropped_tx;
        }
        uint32_t elapsed=now-last_step;
        if (elapsed>=20) {
            cuty_control_tick(&controller,now,elapsed/1000.0f); last_step=now;
            CutySnapshot snapshot={now,rx_errors,dropped_tx,controller};
            if (osMessageQueuePut(snapshots,&snapshot,0,0)!=osOK) ++dropped_tx;
        } else if (controller.safety.state!=CUTY_ACTIVE) {
            cuty_control_tick(&controller,now,0.02f); /* freeze immediately */
        }
        deadline+=10;
        if ((int32_t)(deadline-osKernelGetTickCount())<=0) {
            cuty_control_invalid(&controller); deadline=osKernelGetTickCount()+10;
        }
        osDelayUntil(deadline);
    }
}
static void safety_task(void *unused) {
    (void)unused; uint32_t deadline=osKernelGetTickCount();
    for (;;) {
        osThreadFlagsSet(servo,SUPERVISE);
        deadline+=10;
        if ((int32_t)(deadline-osKernelGetTickCount())<=0) deadline=osKernelGetTickCount()+10;
        osDelayUntil(deadline);
    }
}
static void diagnostics_task(void *unused) {
    (void)unused;
    for (;;) {
        CutySnapshot snapshot;
        if (osMessageQueueGet(snapshots,&snapshot,0,0)==osOK)
            osMessageQueuePut(telemetry,&snapshot,0,0); /* drop, never block control */
        osDelay(200);
    }
}
bool cuty_rtos_create(void) {
    if (created || osKernelGetState()!=osKernelReady || osKernelGetTickFreq()!=1000) return false;
    CutyLimits limits[CUTY_AXES];
    for (unsigned i=0;i<CUTY_AXES;++i) limits[i]=(CutyLimits){-1,1,0.8f,1.5f};
    if (!cuty_control_init(&controller,limits,500,CUTY_FREEZE_COMMAND)) return false;
    rx=osMessageQueueNew(256,sizeof(RxByte),0);
    commands=osMessageQueueNew(8,sizeof(Envelope),0);
    targets=osMessageQueueNew(1,sizeof(Envelope),0);
    snapshots=osMessageQueueNew(1,sizeof(CutySnapshot),0);
    replies=osMessageQueueNew(8,sizeof(CutyReply),0);
    telemetry=osMessageQueueNew(1,sizeof(CutySnapshot),0);
    if (!rx||!commands||!targets||!snapshots||!replies||!telemetry) return false;
    const osThreadAttr_t ca={.name="CommunicationTask",.stack_size=1536,.priority=osPriorityAboveNormal};
    const osThreadAttr_t va={.name="ServoControlTask",.stack_size=1536,.priority=osPriorityHigh};
    const osThreadAttr_t sa={.name="SafetyTask",.stack_size=768,.priority=osPriorityHigh1};
    const osThreadAttr_t da={.name="DiagnosticsTask",.stack_size=1024,.priority=osPriorityLow};
    communication=osThreadNew(communication_task,0,&ca);
    servo=osThreadNew(servo_task,0,&va);
    safety=osThreadNew(safety_task,0,&sa);
    diagnostics=osThreadNew(diagnostics_task,0,&da);
    created=communication&&servo&&safety&&diagnostics;
    /* Any failure is fatal to startup; do not start kernel or retry creation. */
    return created;
}
bool cuty_rtos_start(void) { return created && osKernelStart()==osOK; }

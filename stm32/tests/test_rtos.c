/* Exercise actual adapter control flow with bounded in-memory CMSIS doubles.
 * This is not a preemptive scheduler/ISR/hardware test. */
#include "fakes/cmsis_os2.h"
#include <assert.h>
#include <setjmp.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include "../App/rtos/motion_tasks.c"
/* Board doubles: record what the adapter asks the hardware to do. */
static uint16_t last_pulses[CUTY_AXES]; static bool last_enable, killed; static unsigned output_calls, kicks;
static uint32_t battery_stub; static char uart[4096]; static size_t uart_used;
void cuty_board_info(CutyWireBoot *b) { b->reset=CUTY_RESET_POWER; b->hse=true; b->pwm_build=false; b->sysclk_hz=84000000; }
void cuty_board_set_outputs(const uint16_t p[CUTY_AXES], bool enable) {
    memcpy(last_pulses,p,sizeof last_pulses); last_enable=enable && !killed; ++output_calls; }
void cuty_board_kill_outputs(void) { killed=true; last_enable=false; }
bool cuty_board_outputs_enabled(void) { return last_enable; }
uint32_t cuty_board_battery_mv(void) { return battery_stub; }
void cuty_board_watchdog_kick(void) { ++kicks; }
size_t cuty_board_uart_tx_free(void) { return sizeof uart - uart_used - 1; }
size_t cuty_board_uart_write(const char *d, size_t n) { memcpy(uart+uart_used,d,n); uart_used+=n; uart[uart_used]=0; return n; }
void cuty_board_led(bool on) { (void)on; }
uint32_t cuty_board_heap_min_free(void) { return 12345; }
typedef struct { unsigned capacity,size,count,head; unsigned char *data; } Queue;
typedef struct { void (*function)(void *); void *argument; uint32_t flags; } Thread;
static Queue *allocated[12]; static unsigned allocations;
static Thread threads[5]; static unsigned thread_count;
static Thread *running; static uint32_t tick; static jmp_buf boundary;
osMessageQueueId_t osMessageQueueNew(uint32_t count,uint32_t size,const void *attr) {
    (void)attr; Queue *q=calloc(1,sizeof(*q)); assert(q);
    q->capacity=count; q->size=size; q->data=calloc(count,size); assert(q->data);
    assert(allocations<12); allocated[allocations++]=q; return q;
}
osStatus_t osMessageQueuePut(osMessageQueueId_t id,const void *message,uint8_t priority,uint32_t timeout) {
    (void)priority; assert(timeout==0); Queue *q=id;
    if(q->count==q->capacity) return osErrorResource;
    memcpy(q->data+((q->head+q->count)%q->capacity)*q->size,message,q->size);
    ++q->count; return osOK;
}
osStatus_t osMessageQueueGet(osMessageQueueId_t id,void *message,uint8_t *priority,uint32_t timeout) {
    (void)priority; Queue *q=id;
    if(!q->count) { if(timeout==osWaitForever) longjmp(boundary,1); return osErrorResource; }
    memcpy(message,q->data+q->head*q->size,q->size);
    q->head=(q->head+1)%q->capacity; --q->count; return osOK;
}
osThreadId_t osThreadNew(void (*function)(void *),void *argument,const osThreadAttr_t *attr) {
    assert(thread_count<5 && attr->stack_size>=768);
    Thread *t=&threads[thread_count++]; t->function=function; t->argument=argument; return t;
}
uint32_t osThreadFlagsSet(osThreadId_t id,uint32_t flags) { Thread *t=id; t->flags|=flags; return t->flags; }
uint32_t osThreadFlagsClear(uint32_t flags) { uint32_t old=running->flags; running->flags&=~flags; return old; }
uint32_t osThreadGetStackSpace(osThreadId_t id) { (void)id; return 512; }
uint32_t osKernelGetTickCount(void) { return tick; }
static unsigned delay_budget; /* >0: delays return (advancing time) instead of ending run_once */
uint32_t osKernelGetTickFreq(void) { return 1000; }
osKernelState_t osKernelGetState(void) { return osKernelReady; }
osStatus_t osKernelStart(void) { return osOK; }
osStatus_t osDelay(uint32_t ticks) { if(delay_budget) { --delay_budget; tick+=ticks; return osOK; } longjmp(boundary,1); }
osStatus_t osDelayUntil(uint32_t ticks) { if(delay_budget) { --delay_budget; tick=ticks; return osOK; } longjmp(boundary,1); }
static void run_once(osThreadId_t id) {
    running=id;
    if(!setjmp(boundary)) running->function(running->argument);
}
static void receive(const char *line) {
    for(size_t i=0;i<strlen(line);++i) assert(cuty_uart_rx_isr((uint8_t)line[i]));
}
int main(void) {
    assert(!cuty_uart_rx_isr('x'));
    assert(cuty_rtos_create() && cuty_rtos_start());
    assert(!cuty_rtos_create());
    receive("V2,HB\nV2,ARM\nV2,START\nV2,TARGET,HEAD_PAN,350\n");
    while (((Queue *)rx)->count) run_once(communication);
    assert(((Queue *)targets[CUTY_HEAD_PAN])->count==1); /* overwrite, never FIFO stale goals */
    assert(((Queue *)commands)->count==3);
    run_once(servo);
    assert(controller.safety.state==CUTY_ACTIVE);
    assert(fabs(controller.axes[0].target-0.35)<0.00001);
    CutyReply reply; unsigned replies_read=0;
    while(cuty_take_reply(&reply)) { assert(reply.accepted); ++replies_read; }
    assert(replies_read==4);
    receive("V2,TARGET,LEFT_ARM,200\nV2,TARGET,RIGHT_ARM,-300\n");
    run_once(communication); run_once(servo);
    assert(fabs(controller.axes[CUTY_LEFT_ARM].target-0.2)<0.00001);
    assert(fabs(controller.axes[CUTY_RIGHT_ARM].target+0.3)<0.00001);
    while(cuty_take_reply(&reply)) assert(reply.accepted);
    /* Target before a state transition cannot be applied after re-arm. */
    receive("V2,TARGET,HEAD_PAN,900\nV2,DISARM\nV2,ARM\nV2,START\n");
    run_once(communication); run_once(servo);
    assert(controller.safety.state==CUTY_ACTIVE && controller.axes[0].target==controller.axes[0].commanded);
    receive("V2,TARGET,HEAD_PAN,500\n"); run_once(communication);
    tick=101; run_once(servo); /* stale mailbox goal rejected */
    assert(controller.axes[0].target==controller.axes[0].commanded);
    tick=500; run_once(servo);
    assert(controller.safety.state==CUTY_FAULT);
    CutySnapshot snapshot={tick,0,0,controller,0,false};
    assert(osMessageQueuePut(snapshots,&snapshot,0,0)==osOK);
    run_once(diagnostics);
    assert(cuty_take_telemetry(&snapshot));
    assert(snapshot.controller.safety.state==CUTY_FAULT);
    /* ISR overload cannot block or silently accept bytes. */
    for(unsigned i=0;i<256;++i) assert(cuty_uart_rx_isr('x'));
    assert(!cuty_uart_rx_isr('x')); run_once(servo);
    assert(controller.safety.state==CUTY_FAULT);
    assert(((Queue *)rx)->count==256);
    /* --- additions: TX owner, dry-run gate, liveness, battery, RX resync --- */
    uart_used=0; while(cuty_take_reply(&reply)) {}
    run_once(tx);
    assert(strstr(uart,"V2,BOOT,POWER,HSE,84000000,DRYRUN\n")==uart);
    /* Recover: RESET then HB/ARM/START (fresh timestamps), drain stale RX first. */
    { RxByte junk; while(osMessageQueueGet(rx,&junk,0,0)==osOK) {} rx_lost=false; }
    tick=10000; receive("V2,RESET\nV2,HB\nV2,ARM\nV2,START\n");
    run_once(communication); run_once(servo); run_once(communication); run_once(servo);
    assert(controller.safety.state==CUTY_ACTIVE && controller.safety.fault_reason==CUTY_FAULT_NONE);
    receive("V2,TARGET,HEAD_PAN,350\n"); run_once(communication);
    delay_budget=40; run_once(servo); delay_budget=0; /* 400 ms of 10 ms control polls */
    assert(cuty_control_output_requested(&controller));
    assert(output_calls>0 && !last_enable); /* CUTY_RTOS_DRY_RUN=1: pins never enabled */
    assert(last_pulses[CUTY_HEAD_PAN]>1500 && last_pulses[CUTY_LEFT_ARM]==1500);
    uart_used=0; run_once(tx);
    assert(strstr(uart,"V2,ACK,") && strstr(uart,",TARGET,HEAD_PAN\n"));
    /* Liveness: a fresh servo beat feeds the IWDG, a stale one kills outputs. */
    kicks=0; killed=false; servo_beat_ms=tick; run_once(safety);
    assert(kicks==1 && !killed);
    servo_beat_ms=tick-60; run_once(safety);
    assert(kicks==1 && killed);
    /* Battery: 9.5 V for >1 s raises BATTERY_LOW to the control owner. */
    killed=false; battery_stub=9500; threads[1].flags=0; delay_budget=150; run_once(safety); delay_budget=0;
    assert(threads[1].flags & BATTERY_LOW);
    assert(battery_mv>9000 && battery_mv<10000);
    receive("V2,HB\n"); run_once(communication); servo_beat_ms=tick; run_once(servo);
    assert(controller.safety.state==CUTY_FAULT && controller.safety.fault_reason==CUTY_FAULT_LOW_BATTERY);
    assert(controller.safety.inhibited && !cuty_control_output_requested(&controller));
    receive("V2,RESET\nV2,HB\nV2,ARM\n"); run_once(communication); run_once(servo);
    assert(controller.safety.state==CUTY_DISARMED); /* ARM refused while inhibited */
    /* UART error marker discards the damaged line; next line parses. */
    unsigned before=controller.safety.invalid_commands;
    receive("V2,TARG"); cuty_uart_rx_error_isr(); receive("ET,HEAD_PAN,1\nV2,HB\n");
    run_once(communication); run_once(servo);
    assert(controller.safety.invalid_commands>before);
    /* Split frame: a 60 ms gap inside a line never splices old bytes. */
    receive("V2,H"); tick+=60; receive("B\n"); run_once(communication);
    assert(((Queue *)commands)->count==0);
    for(unsigned i=0;i<allocations;++i) { free(allocated[i]->data); free(allocated[i]); }
    puts("PASS: adapter latest-target queue, barriers, stale goals, replies, snapshots, RX overflow, "
         "TX records, dry-run gate, liveness kill, battery inhibit, RX resync");
    return 0;
}

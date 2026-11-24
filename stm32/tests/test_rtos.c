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
typedef struct { unsigned capacity,size,count,head; unsigned char *data; } Queue;
typedef struct { void (*function)(void *); void *argument; uint32_t flags; } Thread;
static Queue *allocated[16]; static unsigned allocations;
static Thread threads[4]; static unsigned thread_count;
static Thread *running; static uint32_t tick; static jmp_buf boundary;
osMessageQueueId_t osMessageQueueNew(uint32_t count,uint32_t size,const void *attr) {
    (void)attr; Queue *q=calloc(1,sizeof(*q)); assert(q);
    q->capacity=count; q->size=size; q->data=calloc(count,size); assert(q->data);
    assert(allocations<16); allocated[allocations++]=q; return q;
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
    assert(thread_count<4 && attr->stack_size>=768);
    Thread *t=&threads[thread_count++]; t->function=function; t->argument=argument; return t;
}
uint32_t osThreadFlagsSet(osThreadId_t id,uint32_t flags) { Thread *t=id; t->flags|=flags; return t->flags; }
uint32_t osThreadFlagsClear(uint32_t flags) { uint32_t old=running->flags; running->flags&=~flags; return old; }
uint32_t osKernelGetTickCount(void) { return tick; }
uint32_t osKernelGetTickFreq(void) { return 1000; }
osKernelState_t osKernelGetState(void) { return osKernelReady; }
osStatus_t osKernelStart(void) { return osOK; }
osStatus_t osDelay(uint32_t ticks) { (void)ticks; longjmp(boundary,1); }
osStatus_t osDelayUntil(uint32_t ticks) { (void)ticks; longjmp(boundary,1); }
static void run_once(osThreadId_t id) {
    running=id;
    if(!setjmp(boundary)) running->function(running->argument);
}
static void receive(const char *line) {
    for(size_t i=0;i<strlen(line);++i) assert(cuty_uart_rx_isr((uint8_t)line[i]));
}
#ifndef CUTY_TEST_CALIBRATION
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
    receive("V2,START,EXTRA\n"); run_once(communication);
    assert(cuty_take_frame_error());
    run_once(servo);
    assert(controller.safety.state==CUTY_FAULT); /* una trama inválida en ACTIVE enclava el fallo */
    receive("V2,TARGET,LEFT_ARM,200\nV2,TARGET,RIGHT_ARM,-300\n");
    run_once(communication); run_once(servo);
    assert(controller.safety.state==CUTY_FAULT); /* los objetivos no borran FAULT */
    assert(fabs(controller.axes[CUTY_LEFT_ARM].target)<0.00001);
    assert(fabs(controller.axes[CUTY_RIGHT_ARM].target)<0.00001);
    while(cuty_take_reply(&reply)) assert(!reply.accepted);
    receive("V2,DISARM\n"); run_once(communication); run_once(servo);
    assert(controller.safety.state==CUTY_FAULT); /* DISARM tampoco recupera un fallo enclavado */
    receive("V2,RESET\nV2,HB\nV2,ARM\nV2,START\n");
    run_once(communication); run_once(servo);
    assert(controller.safety.state==CUTY_ACTIVE); /* solo RESET + HB + ARM + START recupera */
    while(cuty_take_reply(&reply)) assert(reply.accepted);
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
    CutySnapshot snapshot={tick,0,0,controller};
    assert(osMessageQueuePut(snapshots,&snapshot,0,0)==osOK);
    run_once(diagnostics);
    assert(cuty_take_telemetry(&snapshot));
    assert(snapshot.controller.safety.state==CUTY_FAULT);
    /* ISR overload cannot block or silently accept bytes. */
    for(unsigned i=0;i<256;++i) assert(cuty_uart_rx_isr('x'));
    assert(!cuty_uart_rx_isr('x')); run_once(servo);
    assert(controller.safety.state==CUTY_FAULT);
    assert(((Queue *)rx)->count==256);
    for(unsigned i=0;i<allocations;++i) { free(allocated[i]->data); free(allocated[i]); }
    puts("PASS: adapter latest-target queue, barriers, stale goals, replies, snapshots, RX overflow");
    return 0;
}
#else
static bool physical_on, fail_driver;
static unsigned selected_axis;
static uint16_t physical_pulse;
static unsigned disable_count;
static bool fake_pulse(unsigned axis, uint16_t pulse) {
    physical_on = true; selected_axis = axis; physical_pulse = pulse;
    return !fail_driver;
}
static void fake_disable(void) { physical_on = false; ++disable_count; }
static bool process(const char *line, uint32_t now) {
    tick = now; receive(line);
    while (((Queue *)rx)->count) run_once(communication);
    run_once(servo);
    CutyReply reply; bool accepted = false;
    while (cuty_take_reply(&reply)) accepted = reply.accepted;
    return accepted;
}
static void begin(uint32_t now) {
    assert(process("V2,RESET\nV2,HB\nV2,ARM\nV2,CAL,LEFT_ARM,1500\n", now));
    assert(controller.safety.state == CUTY_READY && physical_on);
    assert(selected_axis == CUTY_LEFT_ARM && physical_pulse == 1500);
}
int main(void) {
    assert(cuty_rtos_set_calibration_driver(fake_pulse, fake_disable));
    assert(cuty_rtos_create());
    assert(!physical_on);
    assert(!process("V2,CAL,LEFT_ARM,1500\n", 0));
    assert(!physical_on);
    assert(process("V2,HB\nV2,ARM\nV2,CAL,LEFT_ARM,1500\n", 0));
    assert(physical_on && controller.safety.state == CUTY_READY);
    assert(process("V2,CAL,LEFT_ARM,1510\n", 100));
    assert(physical_pulse == 1510);
    assert(!process("V2,CAL,RIGHT_ARM,1500\n", 200));
    assert(!physical_on && controller.safety.state == CUTY_FAULT);
    begin(300);
    assert(!process("V2,CAL,LEFT_ARM,1510\n", 310));
    assert(!physical_on); /* Demasiado rápido; nunca aplica el paso. */
    begin(400);
    assert(!process("V2,START\n", 410));
    assert(!physical_on); /* START no puede cambiar de modo con CAL activo. */
    begin(500);
    assert(!process("V2,TARGET,HEAD_PAN,100\n", 510));
    assert(!physical_on);
    begin(600);
    assert(process("V2,DISARM\n", 610));
    assert(!physical_on && controller.safety.state == CUTY_DISARMED);
    assert(process("V2,HB\nV2,ARM\nV2,CAL,LEFT_ARM,1500\n", 700));
    tick = 1200; run_once(servo);
    assert(!physical_on && controller.safety.state == CUTY_FAULT);
    begin(1300);
    process("INVALID\n", 1310);
    assert(!physical_on && controller.safety.state == CUTY_FAULT);
    begin(1400);
    fail_driver = true;
    assert(!process("V2,CAL,LEFT_ARM,1510\n", 1500));
    assert(!physical_on); fail_driver = false;
    begin(1600);
    for (unsigned elapsed = 250; elapsed < CUTY_CAL_SESSION_MS; elapsed += 250)
        assert(process("V2,HB\n", 1600 + elapsed));
    process("V2,HB\n", 1600 + CUTY_CAL_SESSION_MS);
    assert(!physical_on && controller.safety.state == CUTY_FAULT);
    begin(62000);
    for (unsigned i = 0; i < 256; ++i) assert(cuty_uart_rx_isr('x'));
    assert(!cuty_uart_rx_isr('x')); run_once(servo);
    assert(!physical_on && controller.safety.state == CUTY_FAULT && disable_count > 0);
    for (unsigned i = 0; i < allocations; ++i) { free(allocated[i]->data); free(allocated[i]); }
    puts("PASS: CAL arm/HB, one axis, reject START/TARGET, DISARM, timeout, errors, driver failure, RX overflow");
    return 0;
}
#endif

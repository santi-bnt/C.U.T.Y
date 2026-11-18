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
static Queue *allocated[6]; static unsigned allocations;
static Thread threads[4]; static unsigned thread_count;
static Thread *running; static uint32_t tick; static jmp_buf boundary;
osMessageQueueId_t osMessageQueueNew(uint32_t count,uint32_t size,const void *attr) {
    (void)attr; Queue *q=calloc(1,sizeof(*q)); assert(q);
    q->capacity=count; q->size=size; q->data=calloc(count,size); assert(q->data);
    assert(allocations<6); allocated[allocations++]=q; return q;
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
int main(void) {
    assert(!cuty_uart_rx_isr('x'));
    assert(cuty_rtos_create() && cuty_rtos_start());
    assert(!cuty_rtos_create());
    receive("V1,HB\nV1,ARM\nV1,START\nV1,TARGET,0,100\nV1,TARGET,0,350\n");
    run_once(communication);
    assert(((Queue *)targets)->count==1); /* overwrite, never FIFO stale goals */
    assert(((Queue *)commands)->count==3);
    run_once(servo);
    assert(controller.safety.state==CUTY_ACTIVE);
    assert(fabs(controller.axes[0].target-0.35)<0.00001);
    CutyReply reply; unsigned replies_read=0;
    while(cuty_take_reply(&reply)) { assert(reply.accepted); ++replies_read; }
    assert(replies_read==4);
    /* Target before a state transition cannot be applied after re-arm. */
    receive("V1,TARGET,0,900\nV1,DISARM\nV1,ARM\nV1,START\n");
    run_once(communication); run_once(servo);
    assert(controller.safety.state==CUTY_ACTIVE && controller.axes[0].target==controller.axes[0].commanded);
    receive("V1,TARGET,0,500\n"); run_once(communication);
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

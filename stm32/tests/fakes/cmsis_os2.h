/* Minimal host test double. NOT a CMSIS implementation or target header. */
#ifndef TEST_CMSIS_OS2_H
#define TEST_CMSIS_OS2_H
#include <stdint.h>
typedef void *osMessageQueueId_t;
typedef void *osThreadId_t;
typedef enum { osOK=0, osErrorResource=-3 } osStatus_t;
typedef enum { osKernelReady=1 } osKernelState_t;
typedef enum { osPriorityLow=8, osPriorityNormal=24, osPriorityAboveNormal=32, osPriorityHigh=40, osPriorityHigh1=41 } osPriority_t;
typedef struct { const char *name; uint32_t stack_size; osPriority_t priority; } osThreadAttr_t;
#define osWaitForever UINT32_MAX
#define osFlagsError 0x80000000U
osMessageQueueId_t osMessageQueueNew(uint32_t count,uint32_t size,const void *attr);
osStatus_t osMessageQueuePut(osMessageQueueId_t queue,const void *message,uint8_t priority,uint32_t timeout);
osStatus_t osMessageQueueGet(osMessageQueueId_t queue,void *message,uint8_t *priority,uint32_t timeout);
osThreadId_t osThreadNew(void (*function)(void *),void *argument,const osThreadAttr_t *attr);
uint32_t osThreadFlagsSet(osThreadId_t thread,uint32_t flags);
uint32_t osThreadFlagsClear(uint32_t flags);
uint32_t osThreadGetStackSpace(osThreadId_t thread);
uint32_t osKernelGetTickCount(void);
uint32_t osKernelGetTickFreq(void);
osKernelState_t osKernelGetState(void);
osStatus_t osKernelStart(void);
osStatus_t osDelay(uint32_t ticks);
osStatus_t osDelayUntil(uint32_t ticks);
#endif

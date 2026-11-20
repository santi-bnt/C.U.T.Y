/* FreeRTOS configuration for the POSIX simulator (tasks run as pthreads, the
 * tick is a 1 ms SIGALRM timer). Same priorities/tick/hooks as the target so
 * the CMSIS adapter behaves identically; memory sizes are host-sized. */
#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H
#include <stdint.h>

void cuty_fatal(const char *file, int line);

#define configUSE_PREEMPTION                    1
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 0
#define configUSE_TICKLESS_IDLE                 0
#define configTICK_RATE_HZ                      1000U
#define configMAX_PRIORITIES                    56
#define configMINIMAL_STACK_SIZE                1024U
#define configMAX_TASK_NAME_LEN                 18
#define configTICK_TYPE_WIDTH_IN_BITS           TICK_TYPE_WIDTH_32_BITS
#define configIDLE_SHOULD_YIELD                 1
#define configUSE_TASK_NOTIFICATIONS            1
#define configTASK_NOTIFICATION_ARRAY_ENTRIES   1
#define configUSE_MUTEXES                       0
#define configUSE_RECURSIVE_MUTEXES             0
#define configUSE_COUNTING_SEMAPHORES           0
#define configQUEUE_REGISTRY_SIZE               0
#define configUSE_QUEUE_SETS                    0
#define configUSE_TIME_SLICING                  1
#define configENABLE_BACKWARD_COMPATIBILITY     0
#define configSTACK_DEPTH_TYPE                  uint32_t
#define configUSE_EVENT_GROUPS                  0
#define configUSE_STREAM_BUFFERS                0
#define configSUPPORT_STATIC_ALLOCATION         0
#define configSUPPORT_DYNAMIC_ALLOCATION        1
#define configTOTAL_HEAP_SIZE                   ((size_t)(1024U * 1024U))
#define configUSE_IDLE_HOOK                     0
#define configUSE_TICK_HOOK                     0
#define configCHECK_FOR_STACK_OVERFLOW          0  /* pthread stacks */
#define configUSE_MALLOC_FAILED_HOOK            1
#define configUSE_TRACE_FACILITY                0
#define configUSE_CO_ROUTINES                   0
#define configUSE_TIMERS                        0
#define configASSERT(x) do { if (!(x)) cuty_fatal(__FILE__, __LINE__); } while (0)

#define INCLUDE_vTaskDelete                     0
#define INCLUDE_vTaskSuspend                    1
#define INCLUDE_xTaskDelayUntil                 1
#define INCLUDE_vTaskDelay                      1
#define INCLUDE_xTaskGetSchedulerState          1
#define INCLUDE_xTaskGetCurrentTaskHandle       1
#define INCLUDE_uxTaskGetStackHighWaterMark     1
#endif

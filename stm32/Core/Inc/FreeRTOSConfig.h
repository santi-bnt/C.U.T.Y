/* FreeRTOS configuration for the STM32F401CC Black Pill (Cortex-M4F, 84 MHz,
 * 64 KiB RAM). CMSIS-RTOS2 priorities (1..55) are passed straight through,
 * so configMAX_PRIORITIES is 56 and the generic task selector is used. */
#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H
#include <stdint.h>

extern uint32_t SystemCoreClock;
void cuty_fatal(const char *file, int line);

#define configUSE_PREEMPTION                    1
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 0   /* needs <= 32 priorities */
#define configUSE_TICKLESS_IDLE                 0
#define configCPU_CLOCK_HZ                      (SystemCoreClock)
#define configTICK_RATE_HZ                      1000U /* the adapter requires 1 ms ticks */
#define configMAX_PRIORITIES                    56
#define configMINIMAL_STACK_SIZE                128U  /* words */
#define configMAX_TASK_NAME_LEN                 18
#define configTICK_TYPE_WIDTH_IN_BITS           TICK_TYPE_WIDTH_32_BITS
#define configIDLE_SHOULD_YIELD                 1
#define configUSE_TASK_NOTIFICATIONS            1     /* CMSIS thread flags */
#define configTASK_NOTIFICATION_ARRAY_ENTRIES   1
#define configUSE_MUTEXES                       0
#define configUSE_RECURSIVE_MUTEXES             0
#define configUSE_COUNTING_SEMAPHORES           0
#define configQUEUE_REGISTRY_SIZE               0
#define configUSE_QUEUE_SETS                    0
#define configUSE_TIME_SLICING                  1
#define configUSE_NEWLIB_REENTRANT              0
#define configENABLE_BACKWARD_COMPATIBILITY     0
#define configSTACK_DEPTH_TYPE                  uint32_t
#define configUSE_EVENT_GROUPS                  0
#define configUSE_STREAM_BUFFERS                0

/* Memory: heap_4, everything allocated once before the scheduler starts. */
#define configSUPPORT_STATIC_ALLOCATION         0
#define configSUPPORT_DYNAMIC_ALLOCATION        1
#define configTOTAL_HEAP_SIZE                   ((size_t)(24U * 1024U))
#define configAPPLICATION_ALLOCATED_HEAP        0

/* Hooks: any of these is fatal (outputs killed, IWDG resets the MCU). */
#define configUSE_IDLE_HOOK                     0
#define configUSE_TICK_HOOK                     0
#define configCHECK_FOR_STACK_OVERFLOW          2
#define configUSE_MALLOC_FAILED_HOOK            1
#define configUSE_DAEMON_TASK_STARTUP_HOOK      0

#define configGENERATE_RUN_TIME_STATS           0
#define configUSE_TRACE_FACILITY                0
#define configUSE_STATS_FORMATTING_FUNCTIONS    0
#define configUSE_CO_ROUTINES                   0
#define configUSE_TIMERS                        0

/* Cortex-M interrupt priorities: STM32F4 implements 4 priority bits.
 * Any ISR that calls a FromISR API (USART2) must be numerically >= 5. */
#define configPRIO_BITS                         4
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY 15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5
#define configKERNEL_INTERRUPT_PRIORITY         (configLIBRARY_LOWEST_INTERRUPT_PRIORITY << (8 - configPRIO_BITS))
#define configMAX_SYSCALL_INTERRUPT_PRIORITY    (configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << (8 - configPRIO_BITS))

#define configASSERT(x) do { if (!(x)) cuty_fatal(__FILE__, __LINE__); } while (0)

#define INCLUDE_vTaskPrioritySet                0
#define INCLUDE_uxTaskPriorityGet               0
#define INCLUDE_vTaskDelete                     0
#define INCLUDE_vTaskSuspend                    1     /* osWaitForever blocks forever */
#define INCLUDE_xTaskDelayUntil                 1
#define INCLUDE_vTaskDelay                      1
#define INCLUDE_xTaskGetSchedulerState          1
#define INCLUDE_xTaskGetCurrentTaskHandle       1
#define INCLUDE_uxTaskGetStackHighWaterMark     1

/* Map the port handlers onto the CMSIS vector names used by the startup file. */
#define vPortSVCHandler     SVC_Handler
#define xPortPendSVHandler  PendSV_Handler
#define xPortSysTickHandler SysTick_Handler
#endif

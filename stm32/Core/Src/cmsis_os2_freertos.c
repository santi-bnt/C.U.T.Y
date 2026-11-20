/* Minimal CMSIS-RTOS2 API on top of the FreeRTOS kernel.
 *
 * Implements exactly the calls the C.U.T.Y firmware uses, so the adapter in
 * App/rtos keeps the CMSIS-RTOS2 API that STM32CubeMX users know, without
 * pulling in the full ARM CMSIS-FreeRTOS wrapper. Any other CMSIS call fails
 * at link time, on purpose. Shared by the Black Pill image and the POSIX
 * simulator (where "ISR context" never happens).
 *
 *   kernel:  osKernelInitialize/GetState/Start/GetTickCount/GetTickFreq
 *   threads: osThreadNew/GetStackSpace, osThreadFlagsSet/Clear (task notifications)
 *   delays:  osDelay/osDelayUntil
 *   queues:  osMessageQueueNew/Put/Get */
#include "cmsis_os2.h"
#include "FreeRTOS.h"
#include "queue.h"
#include "task.h"

static osKernelState_t kernel_state = osKernelInactive;

static inline int in_isr(void) {
#if defined(__arm__) && !defined(CUTY_SIM)
    uint32_t ipsr;
    __asm volatile ("mrs %0, ipsr" : "=r" (ipsr));
    return ipsr != 0U;
#else
    return 0;
#endif
}

osStatus_t osKernelInitialize(void) {
    if (in_isr()) return osErrorISR;
    if (kernel_state != osKernelInactive) return osError;
    kernel_state = osKernelReady;
    return osOK;
}

osKernelState_t osKernelGetState(void) {
    if (kernel_state == osKernelRunning && xTaskGetSchedulerState() == taskSCHEDULER_SUSPENDED)
        return osKernelLocked;
    return kernel_state;
}

osStatus_t osKernelStart(void) {
    if (in_isr()) return osErrorISR;
    if (kernel_state != osKernelReady) return osError;
    kernel_state = osKernelRunning;
    vTaskStartScheduler(); /* only returns if the idle task could not be created */
    kernel_state = osKernelError;
    return osError;
}

uint32_t osKernelGetTickCount(void) {
    return in_isr() ? (uint32_t)xTaskGetTickCountFromISR() : (uint32_t)xTaskGetTickCount();
}

uint32_t osKernelGetTickFreq(void) { return configTICK_RATE_HZ; }

osThreadId_t osThreadNew(osThreadFunc_t func, void *argument, const osThreadAttr_t *attr) {
    if (in_isr() || func == NULL) return NULL;
    const char *name = (attr != NULL && attr->name != NULL) ? attr->name : "task";
    uint32_t words = (attr != NULL && attr->stack_size != 0U)
        ? attr->stack_size / (uint32_t)sizeof(StackType_t) : configMINIMAL_STACK_SIZE;
    if (words < configMINIMAL_STACK_SIZE) words = configMINIMAL_STACK_SIZE;
    osPriority_t priority = (attr != NULL && attr->priority != osPriorityNone) ? attr->priority : osPriorityNormal;
    if (priority < osPriorityIdle || (int32_t)priority >= configMAX_PRIORITIES) return NULL;
    TaskHandle_t handle = NULL;
    if (xTaskCreate((TaskFunction_t)func, name, (configSTACK_DEPTH_TYPE)words, argument,
                    (UBaseType_t)priority, &handle) != pdPASS) return NULL;
    return (osThreadId_t)handle;
}

uint32_t osThreadGetStackSpace(osThreadId_t thread_id) {
    if (in_isr() || thread_id == NULL) return 0U;
    return (uint32_t)uxTaskGetStackHighWaterMark((TaskHandle_t)thread_id) * (uint32_t)sizeof(StackType_t);
}

uint32_t osThreadFlagsSet(osThreadId_t thread_id, uint32_t flags) {
    TaskHandle_t task = (TaskHandle_t)thread_id;
    uint32_t value = 0U;
    if (task == NULL || (flags & osFlagsError) != 0U) return (uint32_t)osErrorParameter;
    if (in_isr()) {
        BaseType_t woken = pdFALSE;
        (void)xTaskNotifyFromISR(task, flags, eSetBits, &woken);
        (void)xTaskNotifyAndQueryFromISR(task, 0U, eNoAction, &value, NULL);
        portYIELD_FROM_ISR(woken);
    } else {
        (void)xTaskNotify(task, flags, eSetBits);
        (void)xTaskNotifyAndQuery(task, 0U, eNoAction, &value);
    }
    return value;
}

uint32_t osThreadFlagsClear(uint32_t flags) {
    if (in_isr()) return (uint32_t)osErrorISR;
    if ((flags & osFlagsError) != 0U) return (uint32_t)osErrorParameter;
    return (uint32_t)ulTaskNotifyValueClear(NULL, flags); /* value before clearing */
}

osStatus_t osDelay(uint32_t ticks) {
    if (in_isr()) return osErrorISR;
    if (ticks != 0U) vTaskDelay((TickType_t)ticks);
    return osOK;
}

osStatus_t osDelayUntil(uint32_t ticks) {
    if (in_isr()) return osErrorISR;
    TickType_t now = xTaskGetTickCount();
    TickType_t delay = (TickType_t)ticks - now;
    if (delay == 0U || delay > 0x7FFFFFFFU) return osErrorParameter; /* not in the future */
    (void)xTaskDelayUntil(&now, delay);
    return osOK;
}

osMessageQueueId_t osMessageQueueNew(uint32_t msg_count, uint32_t msg_size, const osMessageQueueAttr_t *attr) {
    (void)attr;
    if (in_isr() || msg_count == 0U || msg_size == 0U) return NULL;
    return (osMessageQueueId_t)xQueueCreate((UBaseType_t)msg_count, (UBaseType_t)msg_size);
}

osStatus_t osMessageQueuePut(osMessageQueueId_t mq_id, const void *msg_ptr, uint8_t msg_prio, uint32_t timeout) {
    QueueHandle_t queue = (QueueHandle_t)mq_id;
    (void)msg_prio; /* FIFO only */
    if (queue == NULL || msg_ptr == NULL) return osErrorParameter;
    if (in_isr()) {
        if (timeout != 0U) return osErrorParameter;
        BaseType_t woken = pdFALSE;
        if (xQueueSendToBackFromISR(queue, msg_ptr, &woken) != pdTRUE) return osErrorResource;
        portYIELD_FROM_ISR(woken);
        return osOK;
    }
    if (xQueueSendToBack(queue, msg_ptr, (TickType_t)timeout) != pdPASS)
        return timeout != 0U ? osErrorTimeout : osErrorResource;
    return osOK;
}

osStatus_t osMessageQueueGet(osMessageQueueId_t mq_id, void *msg_ptr, uint8_t *msg_prio, uint32_t timeout) {
    QueueHandle_t queue = (QueueHandle_t)mq_id;
    if (msg_prio != NULL) *msg_prio = 0U;
    if (queue == NULL || msg_ptr == NULL) return osErrorParameter;
    if (in_isr()) {
        if (timeout != 0U) return osErrorParameter;
        BaseType_t woken = pdFALSE;
        if (xQueueReceiveFromISR(queue, msg_ptr, &woken) != pdPASS) return osErrorResource;
        portYIELD_FROM_ISR(woken);
        return osOK;
    }
    /* osWaitForever (0xFFFFFFFF) == portMAX_DELAY: blocks forever (INCLUDE_vTaskSuspend). */
    if (xQueueReceive(queue, msg_ptr, (TickType_t)timeout) != pdPASS)
        return timeout != 0U ? osErrorTimeout : osErrorResource;
    return osOK;
}

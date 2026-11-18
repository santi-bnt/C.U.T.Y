#ifndef CUTY_MOTION_TASKS_H
#define CUTY_MOTION_TASKS_H
#include <stdbool.h>
#include <stdint.h>
#include "../control/body_control.h"
typedef struct {
    uint32_t timestamp_ms, rx_errors, dropped_tx;
    CutyController controller; /* commanded positions only, no measured values */
} CutySnapshot;
typedef struct { uint32_t sequence; bool accepted; } CutyReply;
/* Call after osKernelInitialize, before osKernelStart. Dry-run only. */
bool cuty_rtos_create(void);
bool cuty_rtos_start(void);
/* IRQ-safe only at a FreeRTOS syscall-compatible interrupt priority. */
bool cuty_uart_rx_isr(uint8_t byte);
/* Future UART TX owner consumes records nonblocking. No driver supplied. */
bool cuty_take_reply(CutyReply *reply);
bool cuty_take_telemetry(CutySnapshot *snapshot);
#endif

#ifndef CUTY_MOTION_TASKS_H
#define CUTY_MOTION_TASKS_H
#include <stdbool.h>
#include <stdint.h>
#include "../control/body_control.h"
typedef struct {
    uint32_t timestamp_ms, rx_errors, dropped_tx;
    CutyController controller; /* commanded positions only, no measured values */
    uint32_t battery_mv;       /* filtered pack voltage, 0 = not measured */
    bool output_enabled;       /* PWM physically generated (board gate) */
} CutySnapshot;
typedef struct { uint32_t sequence; bool accepted; CutyCommandKind kind; unsigned axis; } CutyReply;
/* Call after osKernelInitialize, before osKernelStart. Allocation failure is fatal. */
bool cuty_rtos_create(void);
bool cuty_rtos_start(void);
/* USART2 RX interrupt hooks. IRQ-safe only at a FreeRTOS syscall-compatible priority. */
bool cuty_uart_rx_isr(uint8_t byte);
void cuty_uart_rx_error_isr(void); /* framing/noise/overrun: discard the current line */
/* Drained by TxTask (UART TX owner); public for tests. Nonblocking. */
bool cuty_take_reply(CutyReply *reply);
bool cuty_take_telemetry(CutySnapshot *snapshot);
#endif

#ifndef CUTY_MOTION_TASKS_H
#define CUTY_MOTION_TASKS_H
#include <stdbool.h>
#include <stdint.h>
#include "../control/body_control.h"
typedef struct {
    uint32_t timestamp_ms, rx_errors, dropped_tx;
    CutyController controller; /* Consignas calculadas; no son posiciones medidas del servo. */
} CutySnapshot;
typedef struct { uint32_t sequence; bool accepted; CutyState state; } CutyReply;
/* Callbacks de hardware; si quedan nulos, el controlador funciona sin salida física. */
typedef bool (*CutyOutputEnable)(bool explicit_arm, bool heartbeat_fresh, bool safety_ready);
typedef void (*CutyOutputDisable)(void);
typedef bool (*CutyOutputSet)(unsigned axis, float normalized_position);
typedef void (*CutyWatchdogRefresh)(void);
/* Bind board outputs before create. Null callbacks leave this controller dry-run. */
bool cuty_rtos_set_output_driver(CutyOutputEnable enable, CutyOutputDisable disable,
                                 CutyOutputSet set);
bool cuty_rtos_set_watchdog_refresh(CutyWatchdogRefresh refresh);
/* Call after osKernelInitialize, before osKernelStart. */
bool cuty_rtos_create(void);
bool cuty_rtos_start(void);
/* ISR mínima: requiere prioridad NVIC compatible con llamadas al RTOS y timeout cero. */
bool cuty_uart_rx_isr(uint8_t byte);
void cuty_uart_fault_isr(void);
/* Una tarea TX de un solo propietario consume estas colas sin bloquear el control. */
bool cuty_take_reply(CutyReply *reply);
bool cuty_take_telemetry(CutySnapshot *snapshot);
bool cuty_take_frame_error(void);
#endif

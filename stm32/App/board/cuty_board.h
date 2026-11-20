#ifndef CUTY_BOARD_H
#define CUTY_BOARD_H
/* Board services used by the RTOS adapter. Implemented by
 *   Core/Src/board_f401.c  (STM32F401 Black Pill on the C.U.T.Y carrier)
 *   sim/board_sim.c        (FreeRTOS POSIX simulator)
 *   tests/test_rtos.c      (sequential test doubles)
 * The App layer never touches registers directly. */
#include "../communication/wire.h"
#include "../joints.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

void cuty_board_info(CutyWireBoot *info);

/* PWM output stage for J7..J9. enable=false (or a dry-run build) keeps the
 * pins as GPIO driven low: no pulses at all. Pulses are latched by the timer
 * preload at the next 20 ms period. Ignored once outputs were killed. */
void cuty_board_set_outputs(const uint16_t pulse_us[CUTY_AXES], bool enable);
/* Independent cut used by SafetyTask: disable channels, drive pins low and
 * latch until reset. Safe to call from any task. */
void cuty_board_kill_outputs(void);
/* True only if PWM is physically being generated right now. */
bool cuty_board_outputs_enabled(void);

/* Battery voltage at the pack in millivolts (0 if not measurable). */
uint32_t cuty_board_battery_mv(void);

/* Independent watchdog refresh. Only SafetyTask calls it. */
void cuty_board_watchdog_kick(void);

/* Nonblocking UART TX into a driver ring. Only TxTask calls these. */
size_t cuty_board_uart_tx_free(void);
size_t cuty_board_uart_write(const char *data, size_t length);

void cuty_board_led(bool on);

/* Smallest free heap seen since boot (bytes), for V2,DIAG. */
uint32_t cuty_board_heap_min_free(void);
#endif

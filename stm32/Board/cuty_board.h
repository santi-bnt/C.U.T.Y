#ifndef CUTY_BOARD_H
#define CUTY_BOARD_H

#include "stm32f4xx_hal.h"
#include <stdbool.h>

bool cuty_board_init(void);
void cuty_board_safe_state(void);
bool cuty_board_start_uart_rx(void);
void cuty_board_usart2_irq_handler(void);
bool cuty_board_watchdog_init(void);
void cuty_board_watchdog_refresh(void);
void cuty_board_tx_task(void *argument);
TIM_HandleTypeDef *cuty_board_tim4(void);

#endif

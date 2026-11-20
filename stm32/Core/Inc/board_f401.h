#ifndef CUTY_BOARD_F401_H
#define CUTY_BOARD_F401_H
/* STM32F401CC Black Pill on the C.U.T.Y carrier v1.1 (register-level, no HAL).
 *
 *   Clock   25 MHz HSE -> PLL 84 MHz (falls back to HSI 16 MHz if HSE/PLL fail)
 *   USART2  PA2 TX / PA3 RX (AF7), 115200 8N1, RXNE+TXE interrupts, prio 6
 *   TIM4    PB6/PB7/PB8 = CH1..3 (AF2) -> J7 HEAD_PAN, J8 LEFT_ARM, J9 RIGHT_ARM
 *           1 MHz counter, ARR 19999 -> 50 Hz, CCR = pulse in microseconds
 *   J10/J11 PB9 (TIM4_CH4) and PA8 (TIM1_CH1): reserved, held as GPIO low
 *   ADC1    PA1 = ADC1_IN1, battery divider 122/22, 480-cycle sampling
 *   IWDG    LSI/8, reload 999 -> ~250 ms (LSI 17..47 kHz: 170..470 ms)
 *   LED     PC13, active low */
#include <stdbool.h>

#define CUTY_UART_BAUD 115200U

void cuty_board_init(void);           /* clocks + every pin in its safe state */
void cuty_board_watchdog_start(void); /* call right before the scheduler starts */
#endif

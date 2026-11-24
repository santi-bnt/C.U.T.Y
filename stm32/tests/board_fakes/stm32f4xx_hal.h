#ifndef CUTY_TEST_HAL_H
#define CUTY_TEST_HAL_H
#include <stdint.h>
#include <stddef.h>
typedef struct { unsigned Period, Prescaler; } FakeTimerInit;
typedef struct { unsigned Instance; FakeTimerInit Init; } TIM_HandleTypeDef;
typedef struct { uint32_t Pin, Mode, Pull, Speed, Alternate; } GPIO_InitTypeDef;
typedef struct { uint32_t CFGR; } FakeRcc;
extern FakeRcc fake_rcc;
#define RCC (&fake_rcc)
#define RCC_CFGR_PPRE1 0x1C00U
#define TIM4 4U
#define GPIOB 2U
#define GPIO_PIN_6 (1U << 6)
#define GPIO_PIN_7 (1U << 7)
#define GPIO_PIN_8 (1U << 8)
#define GPIO_PIN_RESET 0U
#define GPIO_MODE_OUTPUT_PP 1U
#define GPIO_MODE_AF_PP 2U
#define GPIO_NOPULL 0U
#define GPIO_SPEED_FREQ_LOW 0U
#define GPIO_AF2_TIM4 2U
#define TIM_CHANNEL_1 0U
#define TIM_CHANNEL_2 1U
#define TIM_CHANNEL_3 2U
#define HAL_OK 0
#define HAL_ERROR 1
#define __HAL_RCC_GPIOB_CLK_ENABLE() ((void)0)
void fake_compare(unsigned channel, uint32_t pulse);
#define __HAL_TIM_SET_COMPARE(timer, channel, pulse) fake_compare(channel, pulse)
uint32_t HAL_RCC_GetPCLK1Freq(void);
void HAL_GPIO_WritePin(unsigned port, uint32_t pins, unsigned level);
void HAL_GPIO_Init(unsigned port, GPIO_InitTypeDef *gpio);
int HAL_TIM_PWM_Start(TIM_HandleTypeDef *timer, unsigned channel);
int HAL_TIM_PWM_Stop(TIM_HandleTypeDef *timer, unsigned channel);
#endif

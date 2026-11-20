#include "cuty_board.h"
#include "cuty_servo_output.h"
#include "../App/rtos/motion_tasks.h"
#include "cmsis_os2.h"

void Error_Handler(void);

#ifndef CUTY_PHYSICAL_OUTPUT_ENABLE
#define CUTY_PHYSICAL_OUTPUT_ENABLE 0
#endif

static void SystemClock_Config(void) {
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE2);
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSI;
    /* HSI 16 MHz / 16 * 336 / 4 = 84 MHz; APB1 queda a 42 MHz. */
    osc.PLL.PLLM = 16U;
    osc.PLL.PLLN = 336U;
    osc.PLL.PLLP = RCC_PLLP_DIV4;
    osc.PLL.PLLQ = 7U;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) Error_Handler();
    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK) Error_Handler();
}

static bool output_enable(bool arm, bool heartbeat, bool ready) {
    return cuty_servo_output_enable(arm, heartbeat, ready);
}
static void output_disable(void) { cuty_servo_output_disable(); }
static bool output_set(unsigned axis, float position) {
    return cuty_servo_output_set(axis, position);
}

int main(void) {
    HAL_Init();
    SystemClock_Config();
    if (!cuty_board_init()) Error_Handler();
    if (!cuty_board_watchdog_init()) Error_Handler();
    if (osKernelInitialize() != osOK) Error_Handler();
    if (!cuty_rtos_set_watchdog_refresh(cuty_board_watchdog_refresh)) Error_Handler();
#if CUTY_PHYSICAL_OUTPUT_ENABLE
    if (!cuty_rtos_set_output_driver(output_enable, output_disable, output_set)) Error_Handler();
#else
    /* Por defecto no se enlaza el controlador con TIM4; START solo prueba estados. */
    (void)output_enable; (void)output_disable; (void)output_set;
#endif
    if (!cuty_rtos_create()) Error_Handler();
    const osThreadAttr_t tx_attr = {
        .name = "UartTxTask", .stack_size = 768U, .priority = osPriorityNormal
    };
    if (osThreadNew(cuty_board_tx_task, NULL, &tx_attr) == NULL) Error_Handler();
    if (!cuty_board_start_uart_rx()) Error_Handler();
    if (cuty_rtos_start() != true) Error_Handler();
    Error_Handler();
}

void Error_Handler(void) {
    __disable_irq();
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6 | GPIO_PIN_7 | GPIO_PIN_8, GPIO_PIN_RESET);
    for (;;) { }
}

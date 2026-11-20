#include "cuty_board.h"
#include "cuty_servo_output.h"
#include "servo_calibration.h"
#include "../App/rtos/motion_tasks.h"
#include <stdio.h>
#include <string.h>

#define CUTY_UART_BAUD 115200U
static UART_HandleTypeDef huart2;
static TIM_HandleTypeDef htim4;
static IWDG_HandleTypeDef hiwdg;
static uint8_t uart_rx_byte;
static volatile bool uart_faulted;

static bool uart_transmit_line(const char *line) {
    size_t n = strlen(line);
    return n < 128U && HAL_UART_Transmit(&huart2, (uint8_t *)line, (uint16_t)n, 100U) == HAL_OK;
}

bool cuty_board_init(void) {
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();

    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_6 | GPIO_PIN_7 | GPIO_PIN_8;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_WritePin(GPIOB, gpio.Pin, GPIO_PIN_RESET);
    HAL_GPIO_Init(GPIOB, &gpio);

    gpio.Pin = GPIO_PIN_2 | GPIO_PIN_3;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &gpio);
    HAL_NVIC_SetPriority(USART2_IRQn, 6U, 0U);
    HAL_NVIC_EnableIRQ(USART2_IRQn);

    huart2.Instance = USART2;
    huart2.Init.BaudRate = CUTY_UART_BAUD;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart2) != HAL_OK) return false;

    /* 84 MHz APB1 timer clock / (83+1) = 1 MHz, ARR=19999 => 50 Hz. */
    htim4.Instance = TIM4;
    htim4.Init.Prescaler = 83U;
    htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim4.Init.Period = 19999U;
    htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    if (HAL_TIM_PWM_Init(&htim4) != HAL_OK) return false;
    TIM_OC_InitTypeDef channel = {0};
    channel.OCMode = TIM_OCMODE_PWM1;
    channel.Pulse = 0U;
    channel.OCPolarity = TIM_OCPOLARITY_HIGH;
    channel.OCFastMode = TIM_OCFAST_DISABLE;
    if (HAL_TIM_PWM_ConfigChannel(&htim4, &channel, TIM_CHANNEL_1) != HAL_OK ||
        HAL_TIM_PWM_ConfigChannel(&htim4, &channel, TIM_CHANNEL_2) != HAL_OK ||
        HAL_TIM_PWM_ConfigChannel(&htim4, &channel, TIM_CHANNEL_3) != HAL_OK) return false;
    __HAL_TIM_ENABLE_OCxPRELOAD(&htim4, TIM_CHANNEL_1);
    __HAL_TIM_ENABLE_OCxPRELOAD(&htim4, TIM_CHANNEL_2);
    __HAL_TIM_ENABLE_OCxPRELOAD(&htim4, TIM_CHANNEL_3);
    return cuty_servo_output_init(&htim4, cuty_servo_calibration);
}

TIM_HandleTypeDef *cuty_board_tim4(void) { return &htim4; }

bool cuty_board_start_uart_rx(void) {
    uart_faulted = false;
    return HAL_UART_Receive_IT(&huart2, &uart_rx_byte, 1U) == HAL_OK;
}

bool cuty_board_watchdog_init(void) {
    RCC_OscInitTypeDef osc = {0};
    osc.OscillatorType = RCC_OSCILLATORTYPE_LSI;
    osc.LSIState = RCC_LSI_ON;
    osc.PLL.PLLState = RCC_PLL_NONE;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) return false;
    hiwdg.Instance = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_64;
    hiwdg.Init.Reload = 1000U;
    hiwdg.Init.Window = IWDG_WINDOW_DISABLE;
    return HAL_IWDG_Init(&hiwdg) == HAL_OK;
}

void cuty_board_watchdog_refresh(void) { (void)HAL_IWDG_Refresh(&hiwdg); }

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *handle) {
    if (handle != &huart2) return;
    if (!cuty_uart_rx_isr(uart_rx_byte)) uart_faulted = true;
    if (HAL_UART_Receive_IT(&huart2, &uart_rx_byte, 1U) != HAL_OK) {
        uart_faulted = true;
        cuty_uart_fault_isr();
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *handle) {
    if (handle != &huart2) return;
    uart_faulted = true;
    (void)HAL_UART_AbortReceive(handle);
    cuty_uart_fault_isr();
    (void)HAL_UART_Receive_IT(&huart2, &uart_rx_byte, 1U);
}

static const char *state_name(CutyState state) {
    switch (state) {
    case CUTY_DISARMED: return "DISARMED";
    case CUTY_READY: return "READY";
    case CUTY_ACTIVE: return "ACTIVE";
    case CUTY_FAULT: return "FAULT";
    default: return "UNKNOWN";
    }
}

void cuty_board_tx_task(void *argument) {
    (void)argument;
    uint32_t last_state = UINT32_MAX;
    for (;;) {
        while (cuty_take_frame_error()) {
            (void)uart_transmit_line("V2,NACK,FRAME,UNKNOWN\n");
        }
        CutyReply reply;
        while (cuty_take_reply(&reply)) {
            char line[128];
            (void)snprintf(line, sizeof(line), "V2,%s,%lu,%s,%s\n",
                reply.accepted ? "ACK" : "NACK", (unsigned long)reply.sequence,
                reply.accepted ? "OK" : "REJECTED", state_name(reply.state));
            if (!uart_transmit_line(line)) { uart_faulted = true; cuty_uart_fault_isr(); }
            last_state = (uint32_t)reply.state;
        }
        CutySnapshot snapshot;
        if (cuty_take_telemetry(&snapshot)) {
            char line[160];
            if (last_state != (uint32_t)snapshot.controller.safety.state) {
                (void)snprintf(line, sizeof(line), "V2,STATE,%s,%lu\n",
                    state_name(snapshot.controller.safety.state), (unsigned long)snapshot.timestamp_ms);
                if (!uart_transmit_line(line)) { uart_faulted = true; cuty_uart_fault_isr(); }
                last_state = (uint32_t)snapshot.controller.safety.state;
            }
            (void)snprintf(line, sizeof(line), "V2,TELEM,%lu,%s,%lu,%lu,%ld,%ld,%ld,%s\n",
                (unsigned long)snapshot.timestamp_ms, state_name(snapshot.controller.safety.state),
                (unsigned long)snapshot.rx_errors, (unsigned long)snapshot.dropped_tx,
                (long)(snapshot.controller.axes[0].commanded * 1000.0f),
                (long)(snapshot.controller.axes[1].commanded * 1000.0f),
                (long)(snapshot.controller.axes[2].commanded * 1000.0f),
                uart_faulted ? "UART_FAULT" : "OK");
            if (!uart_transmit_line(line)) { uart_faulted = true; cuty_uart_fault_isr(); }
        }
        osDelay(10U);
    }
}

void USART2_IRQHandler(void) { HAL_UART_IRQHandler(&huart2); }

#include "cuty_board.h"
#include "cmsis_os2.h"
#include "cuty_servo_output.h"
#include "cuty_servo_bench.h"
#include "servo_calibration.h"
#include "../App/rtos/motion_tasks.h"
#include "../App/servos/servo.h"
#include <stdio.h>
#include <string.h>

#define CUTY_UART_BAUD 115200U
static UART_HandleTypeDef huart2;
static TIM_HandleTypeDef htim4;
static uint8_t uart_rx_byte;
static volatile bool uart_faulted;

/* Transmite una línea completa desde la única tarea propietaria del UART TX. */
static bool uart_transmit_line(const char *line) {
    size_t n = strlen(line);
    return n < 128U && HAL_UART_Transmit(&huart2, (uint8_t *)line, (uint16_t)n, 100U) == HAL_OK;
}

bool cuty_board_init(void) {
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();

    /* PB6–PB8 arrancan como salidas digitales bajas; TIM4 no toma los pines aún. */
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

    /* USART2 usa el cruce PA3 RX / PA2 TX hacia los pines 8/10 de la Pi. */
    huart2.Instance = USART2;
    huart2.Init.BaudRate = CUTY_UART_BAUD;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart2) != HAL_OK) return false;

    /* Se deriva el reloj real de TIM4; el contador queda a 1 MHz (1 tick = 1 us). */
    uint32_t tim4_clock_hz = HAL_RCC_GetPCLK1Freq();
    if ((RCC->CFGR & RCC_CFGR_PPRE1) != 0U) tim4_clock_hz *= 2U;
    uint16_t timer_prescaler;
    if (!cuty_servo_timer_prescaler(tim4_clock_hz, 1000000U, &timer_prescaler)) return false;
    htim4.Instance = TIM4;
    htim4.Init.Prescaler = timer_prescaler;
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
    return cuty_servo_output_init(&htim4, cuty_servo_calibration, cuty_servo_test_ranges) &&
           cuty_servo_bench_bind();
}

TIM_HandleTypeDef *cuty_board_tim4(void) { return &htim4; }

void cuty_board_safe_state(void) {
    /* Quita señales TIM4 y devuelve las salidas de la carrier a nivel bajo. */
    cuty_servo_output_disable();
}

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
    /* Acceso directo al IWDG: el snapshot HAL del proyecto no incluye su módulo.
       LSI/64 y reload 1000 dan cerca de 2 s; el LSI tiene tolerancia de frecuencia. */
    /* Arrancar antes de configurar: sin el reloj interno del IWDG, los bits
       PVU/RVU no se limpian y el arranque termina en Error_Handler sin UART RX. */
    IWDG->KR = 0xCCCCU;
    IWDG->KR = 0x5555U;
    IWDG->PR = 4U;
    IWDG->RLR = 1000U;
    uint32_t attempts = 100000U;
    while ((IWDG->SR & (IWDG_SR_PVU | IWDG_SR_RVU)) != 0U && attempts > 0U) {
        --attempts;
    }
    if (attempts == 0U) return false;
    /* Recargar con el periodo nuevo antes de entregar la vigilancia a las tareas. */
    IWDG->KR = 0xAAAAU;
    return true;
}

void cuty_board_watchdog_refresh(void) { IWDG->KR = 0xAAAAU; }

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *handle) {
    if (handle != &huart2) return;
    /* Rearma RX de un byte; el callback no parsea ni transmite desde la interrupción. */
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
        /* UART TX tiene un único dueño para evitar intercalar bytes entre respuestas. */
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
            /* Las posiciones reportadas son consignas, no mediciones del servo. */
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

/* El vector generado por CubeMX delega aquí para no duplicar USART2_IRQHandler. */
void cuty_board_usart2_irq_handler(void) { HAL_UART_IRQHandler(&huart2); }

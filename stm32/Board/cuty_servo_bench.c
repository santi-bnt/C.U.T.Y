#include "cuty_servo_bench.h"
#include "cuty_board.h"
#include "cuty_servo_output.h"
#include "../App/rtos/motion_tasks.h"
#include <math.h>

#ifdef CUTY_BENCH_CHANNEL
#if CUTY_BENCH_CHANNEL < 1 || CUTY_BENCH_CHANNEL > 3
#error CUTY_BENCH_CHANNEL debe ser 1, 2 o 3
#endif

/* Solo para un servo sin carga mecánica: 1500 us es referencia de prueba,
   no un centro medido. -1..1 se limita a 1400..1600 us a 50 Hz.
   Esta ventana tampoco garantiza límites seguros en un mecanismo montado. */
static bool bench_enabled;
static const uint32_t bench_channels[] = {TIM_CHANNEL_1, TIM_CHANNEL_2, TIM_CHANNEL_3};
static const uint16_t bench_pins[] = {GPIO_PIN_6, GPIO_PIN_7, GPIO_PIN_8};

static void bench_disable(void) {
    bench_enabled = false;
    cuty_servo_output_disable();
}

static bool bench_enable(bool explicit_arm, bool heartbeat_fresh, bool safety_ready) {
    if (!explicit_arm || !heartbeat_fresh || !safety_ready) return false;
    TIM_HandleTypeDef *timer = cuty_board_tim4();
    bench_disable();
    __HAL_TIM_SET_COMPARE(timer, bench_channels[CUTY_BENCH_CHANNEL - 1], 1500U);
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = bench_pins[CUTY_BENCH_CHANNEL - 1];
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    gpio.Alternate = GPIO_AF2_TIM4;
    HAL_GPIO_Init(GPIOB, &gpio);
    if (HAL_TIM_PWM_Start(timer, bench_channels[CUTY_BENCH_CHANNEL - 1]) != HAL_OK) {
        bench_disable();
        return false;
    }
    bench_enabled = true;
    return true;
}

static bool bench_set(unsigned axis, float position) {
    if (!bench_enabled || axis >= 3U || !isfinite(position) ||
        position < -1.0f || position > 1.0f) return false;
    /* Los otros ejes siguen siendo lógicos; sus pines permanecen bajos.
       El índice es de canal eléctrico, no identifica el servo conectado. */
    if (axis == CUTY_BENCH_CHANNEL - 1U) {
        uint16_t pulse_us = (uint16_t)lroundf(1500.0f + 100.0f * position);
        __HAL_TIM_SET_COMPARE(cuty_board_tim4(), bench_channels[axis], pulse_us);
    }
    return true;
}
#endif

bool cuty_servo_bench_bind(void) {
#ifdef CUTY_BENCH_CHANNEL
    return cuty_rtos_set_output_driver(bench_enable, bench_disable, bench_set);
#else
    return true;
#endif
}

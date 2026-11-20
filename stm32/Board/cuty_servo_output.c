#include "cuty_servo_output.h"
#include "../App/servos/servo.h"
#include <math.h>
#include <string.h>

#ifndef CUTY_PHYSICAL_OUTPUT_ENABLE
#define CUTY_PHYSICAL_OUTPUT_ENABLE 0
#endif

/* Independent software gate. A reset always leaves channels stopped. */
static TIM_HandleTypeDef *servo_timer;
static CutyServoCalibration cal[3];
static bool initialized;
static bool enabled;
static const uint32_t channels[3] = {TIM_CHANNEL_1, TIM_CHANNEL_2, TIM_CHANNEL_3};

static void pins_safe_low(void) {
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_6 | GPIO_PIN_7 | GPIO_PIN_8;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_WritePin(GPIOB, gpio.Pin, GPIO_PIN_RESET);
    HAL_GPIO_Init(GPIOB, &gpio);
}

bool cuty_servo_output_init(TIM_HandleTypeDef *timer,
                            const CutyServoCalibration calibration[3]) {
    enabled = false;
    initialized = false;
    if (timer == NULL || calibration == NULL || timer->Instance != TIM4 ||
        timer->Init.Prescaler != 83U || timer->Init.Period != 19999U) return false;
    /* Una calibración inválida mantiene el eje bloqueado sin impedir UART de diagnóstico. */
    for (unsigned i = 0; i < 3; ++i) {
        const CutyServoCalibration *c = &calibration[i];
        if (!c->calibration_valid) continue;
        if (c->min_us == 0U || c->max_us >= 20000U || c->min_us >= c->center_us ||
            c->center_us >= c->max_us || c->max_velocity_per_s <= 0.0f ||
            c->max_acceleration_per_s2 <= 0.0f || !isfinite(c->max_velocity_per_s) ||
            !isfinite(c->max_acceleration_per_s2)) return false;
    }
    servo_timer = timer;
    memcpy(cal, calibration, sizeof(cal));
    /* Configure compares at center, but do not start timer output channels. */
    __HAL_RCC_GPIOB_CLK_ENABLE();
    pins_safe_low();
    /* CCR queda preparado, pero HAL_TIM_PWM_Start no se llama durante el arranque. */
    for (unsigned i = 0; i < 3; ++i)
        __HAL_TIM_SET_COMPARE(timer, channels[i], cal[i].calibration_valid ? cal[i].center_us : 0U);
    initialized = true;
    return true;
}

bool cuty_servo_output_enable(bool explicit_arm, bool heartbeat_fresh,
                              bool safety_ready) {
    if (!initialized || !explicit_arm || !heartbeat_fresh || !safety_ready) return false;
/* El interruptor de compilación y la calibración por eje son dos barreras separadas. */
#if !CUTY_PHYSICAL_OUTPUT_ENABLE
    return false;
#else
    for (unsigned i = 0; i < 3; ++i) if (!cal[i].calibration_valid) return false;
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_6 | GPIO_PIN_7 | GPIO_PIN_8;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    gpio.Alternate = GPIO_AF2_TIM4;
    HAL_GPIO_Init(GPIOB, &gpio);
    for (unsigned i = 0; i < 3; ++i) {
        if (HAL_TIM_PWM_Start(servo_timer, channels[i]) != HAL_OK) {
            cuty_servo_output_disable();
            return false;
        }
    }
    enabled = true;
    return true;
#endif
}

void cuty_servo_output_disable(void) {
    enabled = false;
    if (servo_timer == NULL) return;
    for (unsigned i = 0; i < 3; ++i) (void)HAL_TIM_PWM_Stop(servo_timer, channels[i]);
    /* Detener PWM quita la señal; no corta el riel de 6 V ni garantiza torque cero. */
    pins_safe_low();
}

bool cuty_servo_output_set(unsigned axis, float position) {
    if (!enabled || axis >= 3U || !isfinite(position) || position < -1.0f || position > 1.0f)
        return false;
    const CutyServoCalibration *c = &cal[axis];
    uint16_t pulse;
    if (!c->calibration_valid || !cuty_servo_pulse_calibrated(position,c->min_us,c->center_us,
                                                             c->max_us,c->reverse,&pulse)) return false;
    __HAL_TIM_SET_COMPARE(servo_timer, channels[axis], pulse);
    return true;
}

bool cuty_servo_output_is_enabled(void) { return enabled; }

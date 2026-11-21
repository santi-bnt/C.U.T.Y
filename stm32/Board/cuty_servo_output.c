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
static const uint16_t pins[3] = {GPIO_PIN_6, GPIO_PIN_7, GPIO_PIN_8};

static uint32_t tim4_input_clock_hz(void) {
    uint32_t clock_hz = HAL_RCC_GetPCLK1Freq();
    /* En STM32F401, TIM4 recibe PCLK1 si APB1 divide por uno, y 2x PCLK1 si divide más. */
    if ((RCC->CFGR & RCC_CFGR_PPRE1) != 0U) clock_hz *= 2U;
    return clock_hz;
}

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
                            const CutyServoCalibration calibration[3],
                            const CutyServoTestRange test_ranges[3]) {
    enabled = false;
    initialized = false;
    uint16_t expected_prescaler;
    if (timer == NULL || calibration == NULL || test_ranges == NULL || timer->Instance != TIM4 ||
        timer->Init.Period != 19999U ||
        !cuty_servo_timer_prescaler(tim4_input_clock_hz(), 1000000U, &expected_prescaler) ||
        timer->Init.Prescaler != expected_prescaler) return false;
    /* Una calibración inválida mantiene el eje bloqueado sin impedir UART de diagnóstico. */
    uint8_t assigned_servo_mask = 0U;
    for (unsigned i = 0; i < 3; ++i) {
        const CutyServoCalibration *c = &calibration[i];
        const CutyServoTestRange *range = &test_ranges[i];
        if (range->minimum_us == 0U || range->minimum_us >= range->maximum_us ||
            range->maximum_us >= 20000U) return false;
        if (!c->mechanical_calibration_confirmed || !c->joint_mapping_confirmed) continue;
        if (c->test_servo_number == 0U || c->test_servo_number > 3U ||
            c->max_velocity_per_s <= 0.0f ||
            c->max_acceleration_per_s2 <= 0.0f || !isfinite(c->max_velocity_per_s) ||
            !isfinite(c->max_acceleration_per_s2)) return false;
        const uint8_t servo_bit = (uint8_t)(1U << (c->test_servo_number - 1U));
        if ((assigned_servo_mask & servo_bit) != 0U) return false;
        assigned_servo_mask |= servo_bit;
        const CutyServoTestRange *mapped_range = &test_ranges[c->test_servo_number - 1U];
        if (!cuty_servo_limits_within_test_range(c->min_us, c->center_us, c->max_us,
                                                 mapped_range->minimum_us,
                                                 mapped_range->maximum_us)) return false;
    }
    servo_timer = timer;
    memcpy(cal, calibration, sizeof(cal));
    /* Las mediciones no fijan centro; compare queda en cero y los canales detenidos. */
    __HAL_RCC_GPIOB_CLK_ENABLE();
    pins_safe_low();
    /* CCR queda preparado, pero HAL_TIM_PWM_Start no se llama durante el arranque. */
    for (unsigned i = 0; i < 3; ++i)
        __HAL_TIM_SET_COMPARE(timer, channels[i], 0U);
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
    for (unsigned i = 0; i < 3; ++i) {
        if (!cal[i].mechanical_calibration_confirmed || !cal[i].joint_mapping_confirmed) {
            return false;
        }
    }
    cuty_servo_output_disable();
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

bool cuty_servo_output_test_pulse(unsigned test_servo_number, uint16_t pulse_us,
                                 bool explicit_arm, bool heartbeat_fresh,
                                 bool safety_ready) {
    if (!initialized || !explicit_arm || !heartbeat_fresh || !safety_ready ||
        test_servo_number == 0U || test_servo_number > 3U) return false;
#if !CUTY_PHYSICAL_OUTPUT_ENABLE
    return false;
#else
    unsigned axis;
    for (axis = 0U; axis < 3U; ++axis) {
        const CutyServoCalibration *c = &cal[axis];
        if (c->test_servo_number == test_servo_number &&
            c->mechanical_calibration_confirmed && c->joint_mapping_confirmed) break;
    }
    if (axis == 3U || pulse_us < cal[axis].min_us || pulse_us > cal[axis].max_us) return false;

    /* Esta API de banco conmuta un único canal; no realiza barridos ni secuencias. */
    cuty_servo_output_disable();
    __HAL_TIM_SET_COMPARE(servo_timer, channels[axis], pulse_us);
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = pins[axis];
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    gpio.Alternate = GPIO_AF2_TIM4;
    HAL_GPIO_Init(GPIOB, &gpio);
    if (HAL_TIM_PWM_Start(servo_timer, channels[axis]) != HAL_OK) {
        cuty_servo_output_disable();
        return false;
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
    if (!c->mechanical_calibration_confirmed || !c->joint_mapping_confirmed ||
        !cuty_servo_pulse_calibrated(position,c->min_us,c->center_us,
                                                             c->max_us,c->reverse,&pulse)) return false;
    __HAL_TIM_SET_COMPARE(servo_timer, channels[axis], pulse);
    return true;
}

bool cuty_servo_output_is_enabled(void) { return enabled; }

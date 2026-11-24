/* Comprueba el driver real con registros simulados; no demuestra señales físicas. */
#include "../Board/cuty_servo_output.h"
#include "../Board/servo_calibration.h"
#include <assert.h>
#include <stdio.h>

FakeRcc fake_rcc;
static unsigned af_pins, active_mask, starts;
static uint32_t pulses[3];
static bool fail_start;
uint32_t HAL_RCC_GetPCLK1Freq(void) { return 16000000U; }
void fake_compare(unsigned channel, uint32_t pulse) { pulses[channel] = pulse; }
void HAL_GPIO_WritePin(unsigned port, uint32_t pins, unsigned level)
{ assert(port == GPIOB && level == GPIO_PIN_RESET); (void)pins; }
void HAL_GPIO_Init(unsigned port, GPIO_InitTypeDef *gpio) {
    assert(port == GPIOB);
    if (gpio->Mode == GPIO_MODE_AF_PP) {
        assert(gpio->Alternate == GPIO_AF2_TIM4);
        af_pins |= gpio->Pin;
    } else af_pins &= ~gpio->Pin;
}
int HAL_TIM_PWM_Start(TIM_HandleTypeDef *timer, unsigned channel) {
    assert(timer->Instance == TIM4);
    active_mask |= 1U << channel;
    ++starts;
    return fail_start ? HAL_ERROR : HAL_OK;
}
int HAL_TIM_PWM_Stop(TIM_HandleTypeDef *timer, unsigned channel)
{ assert(timer->Instance == TIM4); active_mask &= ~(1U << channel); return HAL_OK; }

int main(void) {
    TIM_HandleTypeDef timer = {TIM4, {19999U, 15U}};
    assert(cuty_servo_output_init(&timer, cuty_servo_calibration, cuty_servo_test_ranges));
    assert(!active_mask && !af_pins && starts == 0);
    assert(!cuty_servo_output_enable(true, true, true)); /* No habilita TARGET automático. */
#if CUTY_CALIBRATION_ENABLE
    for (unsigned axis = 0; axis < 3; ++axis) {
        assert(!cuty_servo_output_calibrate(axis, 1400));
        assert(!active_mask);
        assert(cuty_servo_output_calibrate(axis, 1500));
        assert(active_mask == (1U << axis));
        assert(af_pins == (GPIO_PIN_6 << axis));
        assert(pulses[axis] == 1500);
        unsigned previous_starts = starts;
        assert(cuty_servo_output_calibrate(axis, 1510));
        assert(pulses[axis] == 1510 && starts == previous_starts);
        assert(!cuty_servo_output_calibrate((axis + 1) % 3, 1500));
        assert(!cuty_servo_output_calibrate(axis, 999));
        cuty_servo_output_disable();
        assert(!active_mask && !af_pins && !cuty_servo_output_is_enabled());
    }
    fail_start = true;
    assert(!cuty_servo_output_calibrate(1, 1500));
    assert(!active_mask && !af_pins);
#else
    assert(!cuty_servo_output_calibrate(1, 1500));
    assert(!active_mask && !af_pins && !starts);
#endif
    assert(!cuty_servo_calibration[0].mechanical_calibration_confirmed);
    puts("PASS: board PWM gate, pin mapping, single-channel output, stop and start failure");
    return 0;
}

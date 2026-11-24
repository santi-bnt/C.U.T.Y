#include "servo.h"
#include <math.h>
#include <stddef.h>
bool cuty_servo_pulse(float x,uint16_t lo,uint16_t hi,uint16_t *out) {
    /* Conversión simétrica heredada; es matemática portable, no inicia un timer. */
    if (!out||!isfinite(x)||x < -1||x > 1||!lo||lo>=hi||hi>=20000) return false;
    *out=(uint16_t)lroundf(lo+(x+1)*0.5f*(hi-lo)); return true;
}
bool cuty_servo_pulse_calibrated(float x,uint16_t lo,uint16_t center,uint16_t hi,
                                 bool reverse,uint16_t *out) {
    /* `x` es normalizado [-1,1]; extremos y centro proceden de calibración por eje en microsegundos. */
    if (!out || !isfinite(x) || x < -1.0f || x > 1.0f || !lo ||
        lo >= center || center >= hi || hi >= 20000U) return false;
    if (reverse) x = -x;
    float pulse = x < 0.0f ? center + x * (float)(center-lo)
                           : center + x * (float)(hi-center);
    if (!isfinite(pulse) || pulse < lo || pulse > hi) return false;
    *out=(uint16_t)lroundf(pulse);
    return true;
}

bool cuty_servo_timer_prescaler(uint32_t timer_clock_hz, uint32_t counter_clock_hz,
                               uint16_t *prescaler) {
    /* El contador debe quedar exactamente a 1 MHz para que un tick equivalga a 1 us. */
    if (prescaler == NULL || timer_clock_hz == 0U || counter_clock_hz == 0U ||
        timer_clock_hz < counter_clock_hz || timer_clock_hz % counter_clock_hz != 0U) {
        return false;
    }
    const uint32_t divider = timer_clock_hz / counter_clock_hz;
    if (divider == 0U || divider - 1U > UINT16_MAX) return false;
    *prescaler = (uint16_t)(divider - 1U);
    return true;
}

bool cuty_servo_limits_within_test_range(uint16_t minimum_us, uint16_t center_us,
                                         uint16_t maximum_us, uint16_t tested_minimum_us,
                                         uint16_t tested_maximum_us) {
    /* El centro debe quedar dentro del rango mecánico calibrado y el rango probado. */
    return tested_minimum_us > 0U && tested_minimum_us < tested_maximum_us &&
           minimum_us >= tested_minimum_us && minimum_us < center_us &&
           center_us < maximum_us && maximum_us <= tested_maximum_us &&
           tested_maximum_us < 20000U;
}

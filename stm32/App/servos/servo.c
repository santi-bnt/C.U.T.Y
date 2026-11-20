#include "servo.h"
#include <math.h>
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

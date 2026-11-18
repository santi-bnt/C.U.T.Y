#include "servo.h"
#include <math.h>
bool cuty_servo_pulse(float x,uint16_t lo,uint16_t hi,uint16_t *out) {
    if (!out||!isfinite(x)||x < -1||x > 1||!lo||lo>=hi||hi>=20000) return false;
    *out=(uint16_t)lroundf(lo+(x+1)*0.5f*(hi-lo)); return true;
}

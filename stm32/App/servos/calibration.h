#ifndef CUTY_SERVO_CALIBRATION_H
#define CUTY_SERVO_CALIBRATION_H
/* Joint-space (normalized -1..1) to pulse-width mapping, one entry per joint.
 *
 * Normalized 0 maps to the midpoint of min_us..max_us. The defaults keep that
 * midpoint at 1500 us, the pulse the assembly guide uses to centre each MG996R
 * before the horn, arm or head is screwed on, so 0 is the assembled neutral
 * pose. The +-400 us span (roughly +-36 degrees on an MG996R) is deliberately
 * conservative: widen it per joint only after checking the real mechanism.
 * reversed flips the sign so a positive command can mean the same visual
 * direction on both arms. Signs are NOT yet bench-verified. */
#include "../joints.h"
#include <stdbool.h>
#include <stdint.h>

typedef struct { uint16_t min_us, max_us; bool reversed; } CutyServoCalibration;

#define CUTY_SERVO_CALIBRATION_DEFAULT { \
    /* HEAD_PAN  J7 PB6 */ {1100U, 1900U, false}, \
    /* LEFT_ARM  J8 PB7 */ {1100U, 1900U, false}, \
    /* RIGHT_ARM J9 PB8 */ {1100U, 1900U, false}  \
}

/* Converts all joints; returns false (and leaves out untouched) if any input
 * is non-finite, outside -1..1 or a calibration entry is invalid. */
bool cuty_servo_pulses(const float normalized[CUTY_AXES],
                       const CutyServoCalibration calibration[CUTY_AXES],
                       uint16_t out_us[CUTY_AXES]);
#endif

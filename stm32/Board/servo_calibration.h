#ifndef CUTY_SERVO_CALIBRATION_H
#define CUTY_SERVO_CALIBRATION_H

#include "cuty_servo_output.h"

/* Deliberately invalid until each axis is calibrated on the assembled mechanism. */
static const CutyServoCalibration cuty_servo_calibration[3] = {
    {0U, 0U, 0U, 0.0f, 0.0f, false, false}, /* HEAD_PAN / J7 */
    {0U, 0U, 0U, 0.0f, 0.0f, false, false}, /* LEFT_ARM / J8 */
    {0U, 0U, 0U, 0.0f, 0.0f, false, false}, /* RIGHT_ARM / J9 */
};

#endif

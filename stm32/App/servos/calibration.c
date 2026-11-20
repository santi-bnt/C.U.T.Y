#include "calibration.h"
#include "servo.h"

bool cuty_servo_pulses(const float normalized[CUTY_AXES],
                       const CutyServoCalibration calibration[CUTY_AXES],
                       uint16_t out_us[CUTY_AXES]) {
    uint16_t pulses[CUTY_AXES];
    for (unsigned i = 0; i < CUTY_AXES; ++i) {
        float x = calibration[i].reversed ? -normalized[i] : normalized[i];
        if (calibration[i].min_us < 500U || calibration[i].max_us > 2500U) return false;
        if (!cuty_servo_pulse(x, calibration[i].min_us, calibration[i].max_us, &pulses[i])) return false;
    }
    for (unsigned i = 0; i < CUTY_AXES; ++i) out_us[i] = pulses[i];
    return true;
}

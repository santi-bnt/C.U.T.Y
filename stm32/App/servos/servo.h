#ifndef CUTY_SERVO_H
#define CUTY_SERVO_H
#include <stdbool.h>
#include <stdint.h>
/* Pure conversion; calibration is a caller responsibility. No timer driver. */
bool cuty_servo_pulse(float normalized, uint16_t minimum_us, uint16_t maximum_us, uint16_t *pulse_us);
bool cuty_servo_pulse_calibrated(float normalized, uint16_t minimum_us, uint16_t center_us,
                                 uint16_t maximum_us, bool reverse, uint16_t *pulse_us);
bool cuty_servo_pulse_calibrated(float normalized, uint16_t minimum_us, uint16_t center_us,
                                 uint16_t maximum_us, bool reverse, uint16_t *pulse_us);
#endif

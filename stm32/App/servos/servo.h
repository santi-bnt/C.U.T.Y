#ifndef CUTY_SERVO_H
#define CUTY_SERVO_H
#include <stdbool.h>
#include <stdint.h>
/* Pure conversion; calibration is a caller responsibility. No timer driver. */
bool cuty_servo_pulse(float normalized, uint16_t minimum_us, uint16_t maximum_us, uint16_t *pulse_us);
bool cuty_servo_pulse_calibrated(float normalized, uint16_t minimum_us, uint16_t center_us,
                                 uint16_t maximum_us, bool reverse, uint16_t *pulse_us);
/* Calcula PSC para obtener la frecuencia de contador solicitada sin redondeo. */
bool cuty_servo_timer_prescaler(uint32_t timer_clock_hz, uint32_t counter_clock_hz,
                               uint16_t *prescaler);
/* Comprueba que la calibración mecánica no rebase el rango medido del servo. */
bool cuty_servo_limits_within_test_range(uint16_t minimum_us, uint16_t center_us,
                                         uint16_t maximum_us, uint16_t tested_minimum_us,
                                         uint16_t tested_maximum_us);
#endif

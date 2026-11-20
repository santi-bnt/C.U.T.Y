#ifndef CUTY_SERVO_OUTPUT_H
#define CUTY_SERVO_OUTPUT_H

#include "stm32f4xx_hal.h"
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint16_t min_us;
    uint16_t center_us;
    uint16_t max_us;
    float max_velocity_per_s;
    float max_acceleration_per_s2;
    bool reverse;
    bool calibration_valid;
} CutyServoCalibration;

/* TIM4 CH1/2/3 maps only to J7/J8/J9. J10/J11 are intentionally absent. */
bool cuty_servo_output_init(TIM_HandleTypeDef *timer,
                            const CutyServoCalibration calibration[3]);
bool cuty_servo_output_enable(bool explicit_arm, bool heartbeat_fresh,
                              bool safety_ready);
void cuty_servo_output_disable(void);
bool cuty_servo_output_set(unsigned axis, float normalized_position);
bool cuty_servo_output_is_enabled(void);

#endif

#ifndef CUTY_SERVO_OUTPUT_H
#define CUTY_SERVO_OUTPUT_H

#include "stm32f4xx_hal.h"
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    /* Calibración mecánica del eje; los tres campos quedan sin validar por ahora. */
    uint16_t min_us;
    uint16_t center_us;
    uint16_t max_us;
    float max_velocity_per_s;
    float max_acceleration_per_s2;
    bool reverse;
    bool mechanical_calibration_confirmed;
    bool joint_mapping_confirmed;
    /* Identificador de la prueba 1–3; cero significa que aún no hay asignación. */
    uint8_t test_servo_number;
} CutyServoCalibration;

typedef struct {
    uint16_t minimum_us;
    uint16_t maximum_us;
} CutyServoTestRange;

/* TIM4 CH1/2/3 llega a J7/J8/J9; la correspondencia servo/articulación sigue pendiente. */
bool cuty_servo_output_init(TIM_HandleTypeDef *timer,
                            const CutyServoCalibration calibration[3],
                            const CutyServoTestRange test_ranges[3]);
bool cuty_servo_output_enable(bool explicit_arm, bool heartbeat_fresh,
                              bool safety_ready);
/* Prueba un solo servo identificado; exige las mismas barreras de seguridad. */
bool cuty_servo_output_test_pulse(unsigned test_servo_number, uint16_t pulse_us,
                                 bool explicit_arm, bool heartbeat_fresh,
                                 bool safety_ready);
void cuty_servo_output_disable(void);
bool cuty_servo_output_set(unsigned axis, float normalized_position);
bool cuty_servo_output_is_enabled(void);

#endif

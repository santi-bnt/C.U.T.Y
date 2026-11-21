#ifndef CUTY_SERVO_CALIBRATION_H
#define CUTY_SERVO_CALIBRATION_H

#include "cuty_servo_output.h"

/*
 * Mediciones provisionales de tres servos numerados en una prueba independiente:
 * 1: 1000–2850 us, 2: 1000–2700 us y 3: 1000–2850 us, a 50 Hz.
 * Se observó cerca de 150 grados de recorrido total, pero no se infiere un
 * recorrido de 180 grados ni un centro a 75 grados. Aún faltan centro, sentido,
 * mecanismo y asignación a articulaciones/J7–J9. Por eso ambas confirmaciones
 * son false y las salidas físicas permanecen bloqueadas. Los límites probados son
 * topes de software: no son límites seguros confirmados para el robot.
 */
static const CutyServoTestRange cuty_servo_test_ranges[3] = {
    {1000U, 2850U}, /* Servo de prueba 1 */
    {1000U, 2700U}, /* Servo de prueba 2 */
    {1000U, 2850U}, /* Servo de prueba 3 */
};

/* Configuración por articulación: calibración y mapeo quedan pendientes. */
static const CutyServoCalibration cuty_servo_calibration[3] = {
    {0U, 0U, 0U, 0.0f, 0.0f, false, false, false, 0U}, /* HEAD_PAN */
    {0U, 0U, 0U, 0.0f, 0.0f, false, false, false, 0U}, /* LEFT_ARM */
    {0U, 0U, 0U, 0.0f, 0.0f, false, false, false, 0U}, /* RIGHT_ARM */
};

#endif

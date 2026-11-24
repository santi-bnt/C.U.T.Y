#include "manual_calibration.h"
#include "../joints.h"

bool cuty_calibration_expired(const CutyManualCalibration *session, uint32_t now) {
    return session->active && (uint32_t)(now - session->started_ms) >= CUTY_CAL_SESSION_MS;
}

bool cuty_calibration_request(CutyManualCalibration *session, unsigned axis,
                              uint16_t pulse_us, uint32_t now) {
    if (axis >= CUTY_AXES || pulse_us < CUTY_CAL_MIN_US || pulse_us > CUTY_CAL_MAX_US ||
        cuty_calibration_expired(session, now)) return false;
    if (!session->active) {
        /* La primera orden requiere el mecanismo descargado: no conocemos su posición.
           1500 us es una referencia eléctrica, no el centro mecánico confirmado. */
        if (pulse_us != 1500U) return false;
        *session = (CutyManualCalibration){true, axis, pulse_us, now, now};
        return true;
    }
    int change = (int)pulse_us - (int)session->pulse_us;
    if (session->axis != axis || change < -(int)CUTY_CAL_STEP_US || change > (int)CUTY_CAL_STEP_US)
        return false;
    /* También limita la velocidad de las órdenes crudas: como máximo 10 us/100 ms. */
    if (change && (uint32_t)(now - session->changed_ms) < 100U) return false;
    if (change) session->changed_ms = now;
    session->pulse_us = pulse_us;
    return true;
}

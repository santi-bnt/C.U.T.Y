#ifndef CUTY_MANUAL_CALIBRATION_H
#define CUTY_MANUAL_CALIBRATION_H
#include <stdbool.h>
#include <stdint.h>

/* Ventana de banco, no límites mecánicos confirmados del robot. */
#define CUTY_CAL_MIN_US 1000U
#define CUTY_CAL_MAX_US 2000U
#define CUTY_CAL_STEP_US 10U
#define CUTY_CAL_SESSION_MS 60000U
typedef struct {
    bool active;
    unsigned axis;
    uint16_t pulse_us;
    uint32_t started_ms, changed_ms;
} CutyManualCalibration;

bool cuty_calibration_expired(const CutyManualCalibration *session, uint32_t now);
bool cuty_calibration_request(CutyManualCalibration *session, unsigned axis,
                              uint16_t pulse_us, uint32_t now);
#endif

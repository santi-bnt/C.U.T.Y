#ifndef CUTY_IMU_H
#define CUTY_IMU_H
#include <stdbool.h>
#include <stdint.h>
/* Future interface only: sensor, axes and calibration unspecified. */
typedef struct { uint32_t timestamp_ms; float orientation[3]; bool calibrated; } CutyImuSample;
typedef bool (*CutyImuRead)(CutyImuSample *sample);
#endif

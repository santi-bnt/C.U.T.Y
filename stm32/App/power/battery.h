#ifndef CUTY_BATTERY_H
#define CUTY_BATTERY_H
/* LiPo 3S supervision from the carrier divider on PA1 (ADC1_IN1).
 * Vbat = Vadc * 122 / 22, 12-bit ADC referenced to 3.3 V.
 * Pure logic: the caller supplies millivolts and a millisecond clock. */
#include <stdbool.h>
#include <stdint.h>

#define CUTY_BATTERY_ABSENT_MV     5000U  /* below: USB-only bench, no pack connected */
#define CUTY_BATTERY_LOW_MV       10500U  /* 3.50 V/cell: warning only */
#define CUTY_BATTERY_CRITICAL_MV   9900U  /* 3.30 V/cell: inhibit motion */
#define CUTY_BATTERY_RECOVER_MV   11000U  /* 3.67 V/cell: charged pack clears the latch */
#define CUTY_BATTERY_CRITICAL_MS   1000U  /* must stay low this long (servo current dips) */
#define CUTY_BATTERY_RECOVER_MS    2000U

typedef enum { CUTY_BATTERY_ABSENT, CUTY_BATTERY_OK, CUTY_BATTERY_LOW, CUTY_BATTERY_CRITICAL } CutyBatteryLevel;
typedef enum { CUTY_BATTERY_NO_CHANGE, CUTY_BATTERY_BECAME_CRITICAL, CUTY_BATTERY_RECOVERED } CutyBatteryEvent;

typedef struct {
    uint32_t filtered_mv;
    uint32_t condition_since_ms; /* start of the current below-critical / above-recover run */
    bool primed, in_condition;
    CutyBatteryLevel level;
} CutyBattery;

uint32_t cuty_battery_mv_from_raw(uint16_t raw12);
void cuty_battery_init(CutyBattery *b);
/* Call at a steady rate (10 Hz). Returns transitions into/out of CRITICAL (latched). */
CutyBatteryEvent cuty_battery_update(CutyBattery *b, uint32_t sample_mv, uint32_t now_ms);
#endif

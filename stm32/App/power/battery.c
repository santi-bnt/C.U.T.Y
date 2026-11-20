#include "battery.h"

uint32_t cuty_battery_mv_from_raw(uint16_t raw12) {
    uint32_t raw = raw12 > 4095U ? 4095U : raw12;
    /* 4095 * 3300 * 122 fits in 32 bits (1.65e9). */
    return (raw * 3300U * 122U + (4095U * 22U) / 2U) / (4095U * 22U);
}

void cuty_battery_init(CutyBattery *b) {
    b->filtered_mv = 0; b->condition_since_ms = 0;
    b->primed = false; b->in_condition = false; b->level = CUTY_BATTERY_ABSENT;
}

static CutyBatteryLevel classify(uint32_t mv) {
    if (mv < CUTY_BATTERY_ABSENT_MV) return CUTY_BATTERY_ABSENT;
    if (mv < CUTY_BATTERY_LOW_MV) return CUTY_BATTERY_LOW;
    return CUTY_BATTERY_OK;
}

CutyBatteryEvent cuty_battery_update(CutyBattery *b, uint32_t mv, uint32_t now) {
    /* EMA, alpha = 1/8 (about 0.8 s at 10 Hz); first sample seeds the filter. */
    if (!b->primed) { b->filtered_mv = mv; b->primed = true; }
    else b->filtered_mv = (uint32_t)(((uint64_t)b->filtered_mv * 7U + mv + 4U) / 8U);
    uint32_t f = b->filtered_mv;

    if (b->level == CUTY_BATTERY_CRITICAL) {
        /* Latched: only a pack above RECOVER for RECOVER_MS clears it (unplugged stays latched). */
        bool high = f >= CUTY_BATTERY_RECOVER_MV;
        if (!high) { b->in_condition = false; return CUTY_BATTERY_NO_CHANGE; }
        if (!b->in_condition) { b->in_condition = true; b->condition_since_ms = now; }
        if ((uint32_t)(now - b->condition_since_ms) < CUTY_BATTERY_RECOVER_MS) return CUTY_BATTERY_NO_CHANGE;
        b->in_condition = false; b->level = classify(f);
        return CUTY_BATTERY_RECOVERED;
    }

    bool low = f >= CUTY_BATTERY_ABSENT_MV && f < CUTY_BATTERY_CRITICAL_MV;
    if (low) {
        if (!b->in_condition) { b->in_condition = true; b->condition_since_ms = now; }
        if ((uint32_t)(now - b->condition_since_ms) >= CUTY_BATTERY_CRITICAL_MS) {
            b->in_condition = false; b->level = CUTY_BATTERY_CRITICAL;
            return CUTY_BATTERY_BECAME_CRITICAL;
        }
    } else b->in_condition = false;
    b->level = classify(f);
    return CUTY_BATTERY_NO_CHANGE;
}

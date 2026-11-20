#ifndef CUTY_LIVENESS_H
#define CUTY_LIVENESS_H
/* Task-liveness supervision used by SafetyTask.
 * The supervised task stores a millisecond timestamp every loop (single 32-bit
 * write, atomic on Cortex-M). The supervisor kills the PWM outputs and stops
 * feeding the hardware watchdog once a beat is older than the timeout. The kill
 * is latched: only a reset (IWDG) brings outputs back, disabled. */
#include <stdbool.h>
#include <stdint.h>

#define CUTY_LIVENESS_TIMEOUT_MS 50U   /* ServoControlTask runs every 10 ms */

typedef struct {
    uint32_t timeout_ms;
    bool tripped;
} CutyLiveness;

void cuty_liveness_init(CutyLiveness *l, uint32_t timeout_ms);
/* Returns true while healthy. Once false it stays false (latched). */
bool cuty_liveness_check(CutyLiveness *l, uint32_t last_beat_ms, uint32_t now_ms);
#endif

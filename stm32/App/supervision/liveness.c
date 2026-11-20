#include "liveness.h"

void cuty_liveness_init(CutyLiveness *l, uint32_t timeout_ms) {
    l->timeout_ms = timeout_ms ? timeout_ms : CUTY_LIVENESS_TIMEOUT_MS;
    l->tripped = false;
}

bool cuty_liveness_check(CutyLiveness *l, uint32_t last_beat_ms, uint32_t now_ms) {
    if (l->tripped) return false;
    /* A beat "from the future" (now earlier than the beat) is a fresh beat that
     * raced with this read; wrap-safe signed difference handles it. */
    int32_t age = (int32_t)(now_ms - last_beat_ms);
    if (age > (int32_t)l->timeout_ms) l->tripped = true;
    return !l->tripped;
}

#include "safety.h"
bool cuty_heartbeat_fresh(const CutySafety *s, uint32_t now) {
    return s->heartbeat_seen && (uint32_t)(now-s->last_heartbeat_ms) < s->timeout_ms;
}
void cuty_safety_check(CutySafety *s, uint32_t now) {
    if ((s->state == CUTY_ACTIVE || s->state == CUTY_READY) && !cuty_heartbeat_fresh(s, now)) {
        s->state = CUTY_FAULT;
        if (s->policy == CUTY_RELEASE_OUTPUT) s->output_requested = false;
    }
}

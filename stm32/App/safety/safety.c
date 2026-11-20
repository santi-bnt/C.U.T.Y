#include "safety.h"
bool cuty_heartbeat_fresh(const CutySafety *s, uint32_t now) {
    return s->heartbeat_seen && (uint32_t)(now-s->last_heartbeat_ms) < s->timeout_ms;
}
void cuty_safety_trip(CutySafety *s, CutyFaultReason reason) {
    if (s->state == CUTY_DISARMED) return;
    if (s->state != CUTY_FAULT || s->fault_reason == CUTY_FAULT_NONE) s->fault_reason = reason;
    s->state = CUTY_FAULT;
    if (s->policy == CUTY_RELEASE_OUTPUT) s->output_requested = false;
}
void cuty_safety_check(CutySafety *s, uint32_t now) {
    if (s->state == CUTY_ACTIVE || s->state == CUTY_READY) {
        if (!cuty_heartbeat_fresh(s, now)) cuty_safety_trip(s, CUTY_FAULT_HEARTBEAT_LOST);
        else if (s->inhibited) cuty_safety_trip(s, CUTY_FAULT_LOW_BATTERY);
    }
}
const char *cuty_state_name(CutyState state) {
    switch (state) {
    case CUTY_DISARMED: return "DISARMED";
    case CUTY_READY: return "READY";
    case CUTY_ACTIVE: return "ACTIVE";
    case CUTY_FAULT: return "FAULT";
    default: return "UNKNOWN";
    }
}
const char *cuty_fault_name(CutyFaultReason reason) {
    switch (reason) {
    case CUTY_FAULT_NONE: return "NONE";
    case CUTY_FAULT_INVALID_COMMAND: return "INVALID";
    case CUTY_FAULT_RX_ERROR: return "RX";
    case CUTY_FAULT_STALE_COMMAND: return "STALE";
    case CUTY_FAULT_HEARTBEAT_LOST: return "HEARTBEAT";
    case CUTY_FAULT_CONTROL_OVERRUN: return "OVERRUN";
    case CUTY_FAULT_LIMIT: return "LIMIT";
    case CUTY_FAULT_LOW_BATTERY: return "BATTERY";
    default: return "UNKNOWN";
    }
}

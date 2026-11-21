#include "safety.h"
bool cuty_heartbeat_fresh(const CutySafety *s, uint32_t now) {
    /* La resta unsigned sigue midiendo el intervalo aunque el contador de milisegundos desborde. */
    return s->heartbeat_seen && (uint32_t)(now-s->last_heartbeat_ms) < s->timeout_ms;
}
void cuty_safety_check(CutySafety *s, uint32_t now) {
    /* READY también exige heartbeat para que el enlace no caduque antes de START. */
    if ((s->state == CUTY_ACTIVE || s->state == CUTY_READY) && !cuty_heartbeat_fresh(s, now)) {
        /* FAULT queda enclavado hasta RESET; no se recupera con heartbeat por sí solo. */
        s->state = CUTY_FAULT;
        if (s->policy == CUTY_RELEASE_OUTPUT) s->output_requested = false;
    }
}

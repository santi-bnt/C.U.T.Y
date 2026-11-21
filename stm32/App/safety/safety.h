#ifndef CUTY_SAFETY_H
#define CUTY_SAFETY_H
#include <stdbool.h>
#include <stdint.h>
/* DISARMED -> READY -> ACTIVE requiere HB/ARM/START; FAULT se recupera con RESET. */
typedef enum { CUTY_DISARMED, CUTY_READY, CUTY_ACTIVE, CUTY_FAULT } CutyState;
/* Políticas lógicas; la placa decide el nivel eléctrico y la alimentación del servo. */
typedef enum { CUTY_FREEZE_COMMAND, CUTY_RELEASE_OUTPUT } CutyLossPolicy;
typedef struct {
    CutyState state; CutyLossPolicy policy;
    uint32_t last_heartbeat_ms, timeout_ms, invalid_commands;
    bool heartbeat_seen, output_requested;
} CutySafety;
bool cuty_heartbeat_fresh(const CutySafety *s, uint32_t now);
void cuty_safety_check(CutySafety *s, uint32_t now);
#endif

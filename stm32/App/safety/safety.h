#ifndef CUTY_SAFETY_H
#define CUTY_SAFETY_H
#include <stdbool.h>
#include <stdint.h>
typedef enum { CUTY_DISARMED, CUTY_READY, CUTY_ACTIVE, CUTY_FAULT } CutyState;
typedef enum { CUTY_FREEZE_COMMAND, CUTY_RELEASE_OUTPUT } CutyLossPolicy;
/* First cause that latched FAULT; cleared by RESET. Reported in V2,TEL. */
typedef enum {
    CUTY_FAULT_NONE = 0,
    CUTY_FAULT_INVALID_COMMAND, /* wrong state, out of range or unknown request */
    CUTY_FAULT_RX_ERROR,        /* malformed line, UART error, RX overflow, split frame */
    CUTY_FAULT_STALE_COMMAND,   /* frame older than 100 ms when the control owner saw it */
    CUTY_FAULT_HEARTBEAT_LOST,
    CUTY_FAULT_CONTROL_OVERRUN, /* control deadline missed or bad dt */
    CUTY_FAULT_LIMIT,           /* trajectory would leave the configured bounds */
    CUTY_FAULT_LOW_BATTERY
} CutyFaultReason;
typedef struct {
    CutyState state; CutyLossPolicy policy;
    uint32_t last_heartbeat_ms, timeout_ms, invalid_commands;
    bool heartbeat_seen, output_requested;
    CutyFaultReason fault_reason;
    bool inhibited; /* external interlock (low battery): ARM refused, armed states fault */
} CutySafety;
bool cuty_heartbeat_fresh(const CutySafety *s, uint32_t now);
void cuty_safety_check(CutySafety *s, uint32_t now);
/* Latch FAULT from READY/ACTIVE and remember the first reason. DISARMED stays DISARMED. */
void cuty_safety_trip(CutySafety *s, CutyFaultReason reason);
const char *cuty_state_name(CutyState state);
const char *cuty_fault_name(CutyFaultReason reason);
#endif

#ifndef CUTY_BODY_H
#define CUTY_BODY_H
#include "../communication/uart_protocol.h"
#include "../safety/safety.h"
#include "../joints.h"
#include "fir_filter.h"
typedef struct { float minimum, maximum, max_velocity, max_acceleration; } CutyLimits;
typedef struct { float target, filtered_target, commanded, velocity; } CutyAxis;
typedef struct {
    CutySafety safety; CutyLimits limits[CUTY_AXES]; CutyAxis axes[CUTY_AXES];
    CutyFirFilter head_pan_fir; bool head_pan_fir_enabled; uint32_t steps;
} CutyController;
/* Single owner: all calls serialized by ServoControlTask. No physical PWM here. */
bool cuty_control_init(CutyController *c, const CutyLimits limits[CUTY_AXES], uint32_t timeout_ms, CutyLossPolicy policy);
bool cuty_control_command(CutyController *c, const CutyCommand *cmd, uint32_t now);
void cuty_control_invalid(CutyController *c);
/* Latch FAULT with a reason (no invalid-command count), freeze/release per policy. */
void cuty_control_fault(CutyController *c, CutyFaultReason reason);
/* External interlock, e.g. critically low battery: refuses ARM and faults READY/ACTIVE. */
void cuty_control_set_inhibit(CutyController *c, bool inhibited);
void cuty_control_tick(CutyController *c, uint32_t now, float dt);
bool cuty_control_output_requested(const CutyController *c);
/* A/B switch is serialized with control ticks; enabling seeds history to avoid a reference step. */
bool cuty_control_set_head_fir(CutyController *c, bool enabled);
#endif

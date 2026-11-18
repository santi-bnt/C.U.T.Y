#ifndef CUTY_BODY_H
#define CUTY_BODY_H
#include "../communication/uart_protocol.h"
#include "../safety/safety.h"
#include "../joints.h"
typedef struct { float minimum, maximum, max_velocity, max_acceleration; } CutyLimits;
typedef struct { float target, commanded, velocity; } CutyAxis;
typedef struct {
    CutySafety safety; CutyLimits limits[CUTY_AXES]; CutyAxis axes[CUTY_AXES]; uint32_t steps;
} CutyController;
/* Single owner: all calls serialized by ServoControlTask. No physical PWM here. */
bool cuty_control_init(CutyController *c, const CutyLimits limits[CUTY_AXES], uint32_t timeout_ms, CutyLossPolicy policy);
bool cuty_control_command(CutyController *c, const CutyCommand *cmd, uint32_t now);
void cuty_control_invalid(CutyController *c);
void cuty_control_tick(CutyController *c, uint32_t now, float dt);
bool cuty_control_output_requested(const CutyController *c);
#endif

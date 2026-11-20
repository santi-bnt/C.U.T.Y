#include "body_control.h"
#include <math.h>
#include <string.h>
static float bounded(float x, float lo, float hi) { return fminf(hi, fmaxf(lo, x)); }
static const float head_pan_coefficients[5] = {0.2f, 0.2f, 0.2f, 0.2f, 0.2f};
static void freeze(CutyController *c) {
    for (unsigned i=0; i<CUTY_AXES; ++i) {
        c->axes[i].target=c->axes[i].commanded; c->axes[i].velocity=0;
    }
}
bool cuty_control_init(CutyController *c, const CutyLimits limits[CUTY_AXES], uint32_t timeout, CutyLossPolicy policy) {
    memset(c,0,sizeof(*c)); c->safety.state=CUTY_DISARMED;
    if (!timeout || timeout>60000 || (policy!=CUTY_FREEZE_COMMAND && policy!=CUTY_RELEASE_OUTPUT)) return false;
    for (unsigned i=0; i<CUTY_AXES; ++i) {
        CutyLimits l=limits[i];
        if (!isfinite(l.minimum)||!isfinite(l.maximum)||!isfinite(l.max_velocity)||!isfinite(l.max_acceleration)||
            l.minimum>=l.maximum||l.minimum>0||l.maximum<0||l.max_velocity<=0||l.max_acceleration<=0) return false;
    }
    memcpy(c->limits,limits,sizeof(c->limits)); c->safety.timeout_ms=timeout; c->safety.policy=policy;
    if (!cuty_fir_init(&c->head_pan_fir, head_pan_coefficients, 5U)) return false;
    c->head_pan_fir_enabled = true;
    cuty_fir_reset(&c->head_pan_fir, 0.0f);
    return true;
}
bool cuty_control_set_head_fir(CutyController *c, bool enabled) {
    if (!c) return false;
    if (c->head_pan_fir_enabled != enabled) {
        cuty_fir_reset(&c->head_pan_fir, c->axes[CUTY_HEAD_PAN].target);
        c->head_pan_fir_enabled = enabled;
    }
    return true;
}
void cuty_control_fault(CutyController *c, CutyFaultReason reason) {
    cuty_safety_trip(&c->safety, reason);
    if (c->safety.policy==CUTY_RELEASE_OUTPUT) c->safety.output_requested=false;
    freeze(c);
}
void cuty_control_invalid(CutyController *c) {
    ++c->safety.invalid_commands;
    cuty_control_fault(c, CUTY_FAULT_INVALID_COMMAND);
}
void cuty_control_set_inhibit(CutyController *c, bool inhibited) {
    c->safety.inhibited = inhibited;
    if (inhibited && (c->safety.state==CUTY_READY || c->safety.state==CUTY_ACTIVE))
        cuty_control_fault(c, CUTY_FAULT_LOW_BATTERY);
}
bool cuty_control_command(CutyController *c, const CutyCommand *cmd, uint32_t now) {
    CutySafety *s=&c->safety; cuty_safety_check(s,now);
    switch(cmd->kind) {
    case CUTY_HEARTBEAT: s->heartbeat_seen=true; s->last_heartbeat_ms=now; return true;
    case CUTY_DISARM:
        if (s->state!=CUTY_FAULT) s->state=CUTY_DISARMED;
        s->output_requested=false; freeze(c); return true;
    case CUTY_RESET:
        if (s->state!=CUTY_FAULT) break;
        s->state=CUTY_DISARMED; s->heartbeat_seen=false; s->output_requested=false;
        s->fault_reason=CUTY_FAULT_NONE; freeze(c); return true;
    case CUTY_ARM:
        if (s->state!=CUTY_DISARMED||!cuty_heartbeat_fresh(s,now)||s->inhibited) break;
        s->state=CUTY_READY; freeze(c); return true;
    case CUTY_START:
        if (s->state!=CUTY_READY||!cuty_heartbeat_fresh(s,now)) break;
        s->state=CUTY_ACTIVE; s->output_requested=true; return true;
    case CUTY_TARGET:
        if (s->state!=CUTY_ACTIVE||cmd->axis>=CUTY_AXES||!isfinite(cmd->target)) break;
        if (cmd->target<c->limits[cmd->axis].minimum||cmd->target>c->limits[cmd->axis].maximum) break;
        c->axes[cmd->axis].target=cmd->target; return true;
    default: break;
    }
    cuty_control_invalid(c); return false;
}
void cuty_control_tick(CutyController *c, uint32_t now, float dt) {
    cuty_safety_check(&c->safety,now);
    if (c->safety.state!=CUTY_ACTIVE) {
        cuty_fir_reset(&c->head_pan_fir, c->axes[CUTY_HEAD_PAN].commanded);
        freeze(c); return;
    }
    if (!isfinite(dt)||dt<=0||dt>0.04f) { ++c->safety.invalid_commands; cuty_control_fault(c, CUTY_FAULT_CONTROL_OVERRUN); return; }
    for (unsigned i=0; i<CUTY_AXES; ++i) {
        CutyAxis *a=&c->axes[i]; CutyLimits l=c->limits[i];
        if (i == CUTY_HEAD_PAN && c->head_pan_fir_enabled) {
            float filtered;
            if (!cuty_fir_process(&c->head_pan_fir, a->target, &filtered)) {
                ++c->safety.invalid_commands; cuty_control_fault(c, CUTY_FAULT_LIMIT); return;
            }
            a->filtered_target = bounded(filtered, l.minimum, l.maximum);
        }
        float goal = (i == CUTY_HEAD_PAN && c->head_pan_fir_enabled) ? a->filtered_target : a->target;
        /* Damped setpoint filter; no measured-position feedback or IMU PID. */
        float acc=bounded(4*(goal-a->commanded)-4*a->velocity,-l.max_acceleration,l.max_acceleration);
        float v=bounded(a->velocity+acc*dt,-l.max_velocity,l.max_velocity);
        float p=a->commanded+v*dt;
        if (!isfinite(p)||p<l.minimum||p>l.maximum) { ++c->safety.invalid_commands; cuty_control_fault(c, CUTY_FAULT_LIMIT); return; }
        a->commanded=p; a->velocity=v;
    }
    ++c->steps;
}
bool cuty_control_output_requested(const CutyController *c) {
    return c->safety.output_requested;
}

#include "wire.h"
#include <math.h>

typedef struct { char *out; size_t capacity, used; bool overflow; } Writer;

static void put_char(Writer *w, char c) {
    if (w->used + 1U >= w->capacity) { w->overflow = true; return; }
    w->out[w->used++] = c;
}
static void put_str(Writer *w, const char *s) { while (*s) put_char(w, *s++); }
static void put_u32(Writer *w, uint32_t v) {
    char digits[10]; unsigned n = 0;
    do { digits[n++] = (char)('0' + v % 10U); v /= 10U; } while (v);
    while (n) put_char(w, digits[--n]);
}
static void put_i32(Writer *w, int32_t v) {
    if (v < 0) { put_char(w, '-'); put_u32(w, (uint32_t)(-(int64_t)v)); }
    else put_u32(w, (uint32_t)v);
}
static size_t finish(Writer *w) {
    put_char(w, '\n');
    if (w->capacity) w->out[w->overflow ? 0 : w->used] = '\0';
    return w->overflow ? 0U : w->used;
}

const char *cuty_command_name(CutyCommandKind kind) {
    switch (kind) {
    case CUTY_HEARTBEAT: return "HB";
    case CUTY_ARM: return "ARM";
    case CUTY_START: return "START";
    case CUTY_DISARM: return "DISARM";
    case CUTY_RESET: return "RESET";
    case CUTY_TARGET: return "TARGET";
    default: return "UNKNOWN";
    }
}
const char *cuty_joint_name(unsigned axis) {
    static const char *names[CUTY_AXES] = {"HEAD_PAN", "LEFT_ARM", "RIGHT_ARM"};
    return axis < CUTY_AXES ? names[axis] : "UNKNOWN";
}
const char *cuty_reset_name(CutyResetCause cause) {
    switch (cause) {
    case CUTY_RESET_POWER: return "POWER";
    case CUTY_RESET_PIN: return "PIN";
    case CUTY_RESET_WATCHDOG: return "WATCHDOG";
    case CUTY_RESET_SOFTWARE: return "SOFTWARE";
    case CUTY_RESET_BROWNOUT: return "BROWNOUT";
    default: return "OTHER";
    }
}

int32_t cuty_wire_milli(float x) {
    if (!isfinite(x)) return 0;
    long v = lroundf(x * 1000.0f);
    return (int32_t)(v > 1000 ? 1000 : v < -1000 ? -1000 : v);
}

size_t cuty_wire_reply(char *out, size_t capacity, const CutyWireReply *r) {
    Writer w = {out, capacity, 0, false};
    put_str(&w, r->accepted ? "V2,ACK," : "V2,NAK,");
    put_u32(&w, r->sequence); put_char(&w, ','); put_str(&w, cuty_command_name(r->kind));
    if (r->kind == CUTY_TARGET) { put_char(&w, ','); put_str(&w, cuty_joint_name(r->axis)); }
    return finish(&w);
}

size_t cuty_wire_telemetry(char *out, size_t capacity, const CutyWireTelemetry *t) {
    Writer w = {out, capacity, 0, false};
    put_str(&w, "V2,TEL,"); put_u32(&w, t->timestamp_ms);
    put_char(&w, ','); put_str(&w, cuty_state_name(t->state));
    put_char(&w, ','); put_str(&w, cuty_fault_name(t->reason));
    put_char(&w, ','); put_char(&w, t->output_enabled ? '1' : '0');
    for (unsigned i = 0; i < CUTY_AXES; ++i) { put_char(&w, ','); put_i32(&w, t->commanded_milli[i]); }
    put_char(&w, ','); put_u32(&w, t->battery_mv);
    put_char(&w, ','); put_u32(&w, t->rx_errors);
    put_char(&w, ','); put_u32(&w, t->dropped_tx);
    return finish(&w);
}

size_t cuty_wire_boot(char *out, size_t capacity, const CutyWireBoot *b) {
    Writer w = {out, capacity, 0, false};
    put_str(&w, "V2,BOOT,"); put_str(&w, cuty_reset_name(b->reset));
    put_char(&w, ','); put_str(&w, b->hse ? "HSE" : "HSI");
    put_char(&w, ','); put_u32(&w, b->sysclk_hz);
    put_char(&w, ','); put_str(&w, b->pwm_build ? "PWM" : "DRYRUN");
    return finish(&w);
}

size_t cuty_wire_diag(char *out, size_t capacity, const CutyWireDiag *d) {
    Writer w = {out, capacity, 0, false};
    put_str(&w, "V2,DIAG,"); put_u32(&w, d->timestamp_ms);
    for (unsigned i = 0; i < CUTY_DIAG_TASKS; ++i) { put_char(&w, ','); put_u32(&w, d->stack_free_bytes[i]); }
    put_char(&w, ','); put_u32(&w, d->heap_min_free_bytes);
    put_char(&w, ','); put_u32(&w, d->rx_overflows);
    put_char(&w, ','); put_u32(&w, d->tx_overflows);
    return finish(&w);
}

#ifndef CUTY_WIRE_H
#define CUTY_WIRE_H
/* Outgoing V2 records (STM32 -> Raspberry). Pure formatting, no I/O, no printf.
 * Every record is one ASCII line ending in LF. Functions return the length
 * written (without NUL) or 0 if the buffer is too small; output is always
 * NUL-terminated when capacity > 0. */
#include "uart_protocol.h"
#include "../safety/safety.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CUTY_WIRE_LINE_MAX 112U

typedef struct {
    uint32_t sequence;      /* valid frames counted since boot */
    bool accepted;
    CutyCommandKind kind;
    unsigned axis;          /* only meaningful for CUTY_TARGET */
} CutyWireReply;

typedef struct {
    uint32_t timestamp_ms;
    CutyState state;
    CutyFaultReason reason;
    bool output_enabled;            /* physical PWM gate as reported by the board */
    int32_t commanded_milli[CUTY_AXES]; /* same unit as V2,TARGET */
    uint32_t battery_mv;
    uint32_t rx_errors, dropped_tx;
} CutyWireTelemetry;

typedef enum { CUTY_RESET_POWER, CUTY_RESET_PIN, CUTY_RESET_WATCHDOG, CUTY_RESET_SOFTWARE,
               CUTY_RESET_BROWNOUT, CUTY_RESET_OTHER } CutyResetCause;

typedef struct {
    CutyResetCause reset;
    bool hse;              /* true: 25 MHz crystal PLL; false: HSI fallback */
    bool pwm_build;        /* false: dry-run image, PWM pins never leave GPIO low */
    uint32_t sysclk_hz;
} CutyWireBoot;

#define CUTY_DIAG_TASKS 5U
typedef struct {
    uint32_t timestamp_ms;
    uint32_t stack_free_bytes[CUTY_DIAG_TASKS]; /* COM, SRV, SAF, DIA, TX */
    uint32_t heap_min_free_bytes;
    uint32_t rx_overflows, tx_overflows;
} CutyWireDiag;

const char *cuty_command_name(CutyCommandKind kind);
const char *cuty_joint_name(unsigned axis);
const char *cuty_reset_name(CutyResetCause cause);
size_t cuty_wire_reply(char *out, size_t capacity, const CutyWireReply *reply);
size_t cuty_wire_telemetry(char *out, size_t capacity, const CutyWireTelemetry *t);
size_t cuty_wire_boot(char *out, size_t capacity, const CutyWireBoot *boot);
size_t cuty_wire_diag(char *out, size_t capacity, const CutyWireDiag *d);
/* Normalized position -> integer milli-units, rounded, clamped to +-1000. */
int32_t cuty_wire_milli(float normalized);
#endif

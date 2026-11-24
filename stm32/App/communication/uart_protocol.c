#include "uart_protocol.h"
#include <string.h>

/* Acepta únicamente V2: ASCII, hasta 63 bytes útiles y posiciones enteras entre -1000 y 1000. */
bool cuty_parse_line(const char *s, CutyCommand *out) {
    static const char *names[] = {"V2,HB", "V2,ARM", "V2,START", "V2,DISARM", "V2,RESET"};
    if (!s || !out) return false;
    CutyCommand c = {0};
    for (unsigned i = 0; i < sizeof(names)/sizeof(names[0]); ++i) {
        if (!strcmp(s, names[i])) { c.kind = (CutyCommandKind)i; *out = c; return true; }
    }
    if (!strcmp(s, "V2,INFO")) { c.kind = CUTY_INFO; *out = c; return true; }
    bool calibration = strncmp(s, "V2,CAL,", 7) == 0;
    if (!calibration && strncmp(s, "V2,TARGET,", 10)) return false;
    s += calibration ? 7 : 10;
    static const char *joints[CUTY_AXES] = {"HEAD_PAN", "LEFT_ARM", "RIGHT_ARM"};
    unsigned axis;
    for (axis = 0; axis < CUTY_AXES; ++axis) {
        size_t length = strlen(joints[axis]);
        if (!strncmp(s, joints[axis], length) && s[length] == ',') {
            c.axis = axis; s += length + 1; break;
        }
    }
    if (axis == CUTY_AXES) return false;
    if (calibration) {
        /* CAL usa exactamente cuatro dígitos en microsegundos, sin signo. */
        unsigned value = 0;
        for (unsigned i = 0; i < 4; ++i) {
            if (*s < '0' || *s > '9') return false;
            value = value * 10U + (unsigned)(*s++ - '0');
        }
        if (*s || value < 1000U || value > 2000U) return false;
        c.kind = CUTY_CALIBRATE; c.pulse_us = (uint16_t)value;
        *out = c; return true;
    }
    /* El valor del cable está en milésimas; el controlador trabaja en unidades normalizadas. */
    bool negative = *s == '-'; if (negative) ++s;
    int value = 0; unsigned digits = 0;
    while (*s >= '0' && *s <= '9') {
        if (++digits > 4) return false;
        value = value * 10 + (*s++ - '0');
    }
    if (*s || !digits || value > 1000) return false;
    c.kind = CUTY_TARGET; c.target = (negative ? -value : value)/1000.0f;
    *out = c; return true;
}
CutyRxResult cuty_rx_byte(CutyParser *p, uint8_t byte, CutyCommand *out) {
    if (byte == '\n') {
        bool valid = false;
        if (!p->dropping) {
            if (p->used && p->line[p->used-1] == '\r') --p->used;
            p->line[p->used] = 0; valid = cuty_parse_line(p->line, out);
        }
        p->used = 0; p->dropping = false;
        return valid ? CUTY_RX_COMMAND : CUTY_RX_ERROR;
    }
    /* Tras NUL, no ASCII o exceso de longitud, descarta todo el resto hasta LF para resincronizar. */
    if (p->dropping) return CUTY_RX_NONE;
    if (!byte || byte > 127 || p->used >= CUTY_LINE_CAPACITY-1) { p->dropping = true; return CUTY_RX_NONE; }
    p->line[p->used++] = (char)byte; return CUTY_RX_NONE;
}

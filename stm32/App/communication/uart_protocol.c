#include "uart_protocol.h"
#include <string.h>
bool cuty_parse_line(const char *s, CutyCommand *out) {
    static const char *names[] = {"V2,HB", "V2,ARM", "V2,START", "V2,DISARM", "V2,RESET"};
    if (!s || !out) return false;
    CutyCommand c = {0};
    for (unsigned i = 0; i < sizeof(names)/sizeof(names[0]); ++i) {
        if (!strcmp(s, names[i])) { c.kind = (CutyCommandKind)i; *out = c; return true; }
    }
    if (strncmp(s, "V2,TARGET,", 10)) return false;
    s += 10;
    static const char *joints[CUTY_AXES] = {"HEAD_PAN", "LEFT_ARM", "RIGHT_ARM"};
    unsigned axis;
    for (axis = 0; axis < CUTY_AXES; ++axis) {
        size_t length = strlen(joints[axis]);
        if (!strncmp(s, joints[axis], length) && s[length] == ',') {
            c.axis = axis; s += length + 1; break;
        }
    }
    if (axis == CUTY_AXES) return false;
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
    if (p->dropping) return CUTY_RX_NONE;
    if (!byte || byte > 127 || p->used >= CUTY_LINE_CAPACITY-1) { p->dropping = true; return CUTY_RX_NONE; }
    p->line[p->used++] = (char)byte; return CUTY_RX_NONE;
}

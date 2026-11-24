#ifndef CUTY_UART_H
#define CUTY_UART_H
#include "../joints.h"
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#define CUTY_LINE_CAPACITY 64
/* TARGET transmite enteros en milésimas; el controlador usa valores float normalizados. */
typedef enum { CUTY_HEARTBEAT, CUTY_ARM, CUTY_START, CUTY_DISARM, CUTY_RESET, CUTY_TARGET, CUTY_CALIBRATE } CutyCommandKind;
typedef struct { CutyCommandKind kind; unsigned axis; float target; uint16_t pulse_us; } CutyCommand;
typedef enum { CUTY_RX_NONE, CUTY_RX_COMMAND, CUTY_RX_ERROR } CutyRxResult;
typedef struct { char line[CUTY_LINE_CAPACITY]; size_t used; bool dropping; } CutyParser;
bool cuty_parse_line(const char *line, CutyCommand *command);
CutyRxResult cuty_rx_byte(CutyParser *parser, uint8_t byte, CutyCommand *command);
#endif

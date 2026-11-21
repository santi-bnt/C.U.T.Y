#include "servo_command.h"
#include <string.h>

/* Protocolo de prueba: PING, STOP o SERVO,numero,microsegundos. */
ServoCommand servo_parse_command(const char *line)
{
    ServoCommand command = {COMMAND_INVALID, 0, 0};
    if (strcmp(line, "PING") == 0) {
        command.type = COMMAND_PING;
    } else if (strcmp(line, "STOP") == 0) {
        command.type = COMMAND_STOP;
    } else if (strncmp(line, "SERVO,", 6) == 0) {
        const char *p = line + 6;
        if (*p < '1' || *p > '3') return command;
        command.servo = (unsigned int)(*p++ - '0');
        if (*p++ != ',') return command;

        /* Exigimos exactamente cuatro digitos para evitar entradas ambiguas. */
        for (unsigned int i = 0; i < 4; ++i) {
            if (*p < '0' || *p > '9') return command;
            command.pulse_us = command.pulse_us * 10 + (unsigned int)(*p++ - '0');
        }
        if (*p == '\0' && command.pulse_us >= 1000 && command.pulse_us <= 2000) {
            command.type = COMMAND_SERVO;
        }
    }
    return command;
}

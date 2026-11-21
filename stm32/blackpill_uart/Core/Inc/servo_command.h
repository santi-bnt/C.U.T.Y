#ifndef SERVO_COMMAND_H
#define SERVO_COMMAND_H

typedef enum { COMMAND_INVALID, COMMAND_PING, COMMAND_STOP, COMMAND_SERVO } CommandType;
typedef struct {
    CommandType type;
    unsigned int servo;       /* Numero impreso en la guia: 1, 2 o 3. */
    unsigned int pulse_us;    /* Ancho del pulso, no grados. */
} ServoCommand;

ServoCommand servo_parse_command(const char *line);

#endif

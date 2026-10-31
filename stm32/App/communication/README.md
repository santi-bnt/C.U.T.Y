# STM32 Communication

Future UART receive/transmit, framing, validation, command dispatch, and telemetry emission. C/H templates contain no parser.

Consume high-level commands and emit measured state. Do not treat incoming data as direct PWM authority. Validate frame length, command shape, units and limits before dispatch; exact rules are not finalized.

See [protocol](../../../docs/protocol/protocol.md). Baud rate, acknowledgement/error handling, checksum, and binary framing remain open.

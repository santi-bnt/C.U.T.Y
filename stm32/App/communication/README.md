# STM32 Communication

Portable V2 framing and parsing now exist in uart_protocol.c/.h. The CMSIS dry-run adapter queues validated commands; physical UART RX/TX drivers remain pending.

Consume high-level targets; distinguish commanded state from unavailable measurements. V2 uses normalized milli-units, not degrees or direct PWM. See [architecture and experimental grammar](../../../docs/freertos-motion-control.md).

See [protocol](../../../docs/protocol/protocol.md). Baud rate, acknowledgement/error handling, checksum, and binary framing remain open.

# STM32 Communication

Portable V2 framing and parsing live in `uart_protocol.c/.h`. The CMSIS adapter queues validated commands; the `stm32/blackpill_uart` board application connects them to USART2 RX/TX and emits ACK/NACK/STATE/TELEM replies.

Consume high-level targets; distinguish commanded state from unavailable measurements. V2 uses normalized milli-units, not degrees or direct PWM. See [architecture and experimental grammar](../../../docs/freertos-motion-control.md).

V2 uses 115200 baud, LF-framed ASCII, sequence ACK/NACK, state and commanded-position telemetry. CRC/session authentication and protection against corrupted-but-valid text remain outside this experimental protocol. See [protocol implementation and risks](../../../docs/freertos-motion-control.md) and [board setup](../../../stm32/blackpill_uart/README.md).

# STM32 Communication

`uart_protocol.c/.h` frame and parse Raspberry → STM32 V2 lines. `wire.c/.h` format the STM32 → Raspberry records (`BOOT`, `ACK`/`NAK`, `TEL`, `DIAG`) without printf. The USART2 driver is in `Core/Src/board_f401.c`.

Consume high-level targets; distinguish commanded state from unavailable measurements. V2 uses normalized milli-units, not degrees or direct PWM. See [architecture and experimental grammar](../../../docs/freertos-motion-control.md).

115200 8N1, no checksum yet. Full record list: [FreeRTOS firmware](../../../docs/freertos-motion-control.md#wire-protocol-v2).

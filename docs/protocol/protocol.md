# Protocolo UART V2

Status: V2 parser, USART2 board adapter, response encoder and Raspberry serializer are implemented. Raspberry/Black Pill UART communication and the three carrier servo channels were previously exercised physically; the current integrated firmware/profile and final safety behavior still require supervised validation. V2 is not wire-compatible with historical `SET_*` examples below.

Raspberry sends high-level goals; STM32 converts them into safe physical movement and emits status/measurements. Do not stream raw servo PWM continuously from Raspberry.

Historical discussion examples (not accepted by V2):
```text
SET_HEAD_PAN,15
SET_LEFT_ARM,8
SET_RIGHT_ARM,-8
STATUS,OK
```
Current V2 input format: LF terminated, optional CR before LF; `V2,HB`, `V2,INFO`, `V2,ARM`, `V2,START`, `V2,DISARM`, `V2,RESET`, and `V2,TARGET,<HEAD_PAN|LEFT_ARM|RIGHT_ARM>,<signed milli-unit integer>`. See [motion control](../freertos-motion-control.md) for the exact parser grammar. The old examples are not accepted by the V2 parser.

See [commands](commands.md) and [telemetry](telemetry.md).

## Checks before final physical operation

- Confirm the carrier design target STM32F401CCU6 against the actual module marking/revision and validate PA3/PA2 continuity, 115200 8N1, 3.3 V levels and common GND before live use.
- Per-axis neutral, direction and mechanically safe limits must come from physical calibration.
- The Raspberry executor checks the `V2,INFO` SHA-256 fingerprint against its loaded profile before authorizing robot mode. A matching fingerprint proves file/build correspondence only; it does not validate the measured mechanics.
- Exercise heartbeat timeout, UART loss, FAULT and explicit recovery on the assembled hardware.
- Confirm actual telemetry freshness and UART error behavior under sustained operation.

Firmware validates commands and applies configured limits locally. The optional Raspberry dashboard endpoint is read-only and is not part of a real-time control loop.

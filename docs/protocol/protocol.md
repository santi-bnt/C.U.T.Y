# Proposed Human-Readable UART Protocol

Status: experimental V2 is implemented in the portable STM32 parser and Raspberry serializer; physical UART driver/firmware image and response encoder remain pending. V2 is the current code reference and is not wire-compatible with the historical `SET_*` examples below.

Raspberry sends high-level goals; STM32 converts them into safe physical movement and emits status/measurements. Do not stream raw servo PWM continuously from Raspberry.

Historical discussion examples (not accepted by V2):
```text
SET_HEAD_PAN,15
SET_LEFT_ARM,8
SET_RIGHT_ARM,-8
STATUS,OK
```
Current V2 input format: LF terminated, optional CR before LF; `V2,HB`, `V2,ARM`, `V2,START`, `V2,DISARM`, `V2,RESET`, and `V2,TARGET,<HEAD_PAN|LEFT_ARM|RIGHT_ARM>,<signed milli-unit integer>`. See [motion control](../freertos-motion-control.md) for the exact parser grammar. The old examples are not accepted by the V2 parser.

See [commands](commands.md) and [telemetry](telemetry.md).

## Decisions required before implementation

- Confirm the carrier design target STM32F401CCU6 against the actual module marking/revision and validate PA3/PA2 continuity, 115200 8N1, 3.3 V levels and common GND before live use.
- Units, coordinate frames, calibrated limits, and target versus measured meaning.
- Startup/version negotiation, acknowledgements, errors, sequencing, retries.
- Heartbeat, stale command timeout, disconnect behavior, and recovery.
- Framing, partial/truncated/invalid data, bounds, overflow, and checksum policy.
- Telemetry rates, timestamps, validity, and safety-state reporting.
- Whether a binary format is later needed; do not finalize it in this task.

Firmware must validate commands and apply safety limits locally. The future dashboard is not part of a real-time control loop.

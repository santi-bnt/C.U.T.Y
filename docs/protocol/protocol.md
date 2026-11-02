# Proposed Human-Readable UART Protocol

Status: design sketch only. No UART implementation or finalized binary protocol exists.

Raspberry sends high-level goals; STM32 converts them into safe physical movement and emits status/measurements. Do not stream raw servo PWM continuously from Raspberry.

Initial discussion format: one comma-separated ASCII-compatible text record per line, terminated by LF. Examples:
```text
SET_HEAD,15,-4
STATUS,OK
```
Names are uppercase; example decimals use a dot. Exact CRLF tolerance, field grammar, maximum line length, units, and parser rules are not yet agreed. These examples are not a parser specification.

See [commands](commands.md) and [telemetry](telemetry.md).

## Decisions required before implementation

- STM32H7 board, UART pins, baud rate, electrical levels and grounding.
- Units, coordinate frames, calibrated limits, and target versus measured meaning.
- Startup/version negotiation, acknowledgements, errors, sequencing, retries.
- Heartbeat, stale command timeout, disconnect behavior, and recovery.
- Framing, partial/truncated/invalid data, bounds, overflow, and checksum policy.
- Telemetry rates, timestamps, validity, and safety-state reporting.
- Whether a binary format is later needed; do not finalize it in this task.

Firmware must validate commands and apply safety limits locally. The future dashboard is not part of a real-time control loop.

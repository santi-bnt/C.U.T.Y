# Proposed Human-Readable UART Protocol

Status: superseded by the implemented V2 line protocol (115200 8N1). See [the firmware doc](../freertos-motion-control.md#wire-protocol-v2). The notes below record the original open questions.

Raspberry sends high-level goals; STM32 converts them into safe physical movement and emits status/measurements. Do not stream raw servo PWM continuously from Raspberry.

Initial discussion format: one comma-separated ASCII-compatible text record per line, terminated by LF. These are illustrative single-axis records for the three active joints:
```text
SET_HEAD_PAN,15
SET_LEFT_ARM,8
SET_RIGHT_ARM,-8
STATUS,OK
```
Names are uppercase; example decimals use a dot. Exact CRLF tolerance, field grammar, maximum line length, units, and parser rules are not yet agreed. These examples are not a parser specification. The base, pedestal and torso are fixed; old `SET_HEAD` PAN/TILT and `SET_BODY` examples are superseded.

See [commands](commands.md) and [telemetry](telemetry.md).

## Decisions required before implementation

- Confirm the exact STM32F401 Black Pill variant/revision and validate the carrier's proposed UART mapping (Pi TX pin 8 to PA3, PA2 to Pi RX pin 10), baud rate, electrical levels and grounding before implementing firmware.
- Units, coordinate frames, calibrated limits, and target versus measured meaning.
- Startup/version negotiation, acknowledgements, errors, sequencing, retries.
- Heartbeat, stale command timeout, disconnect behavior, and recovery.
- Framing, partial/truncated/invalid data, bounds, overflow, and checksum policy.
- Telemetry rates, timestamps, validity, and safety-state reporting.
- Whether a binary format is later needed; do not finalize it in this task.

Firmware must validate commands and apply safety limits locally. The future dashboard is not part of a real-time control loop.

# Proposed High-Level Commands

Status: table below is historical and not accepted by the implemented experimental V2 parser. V2 commands are documented in [motion control](../freertos-motion-control.md). The normal firmware provides HAL UART and keeps PWM blocked; the separate manual build adds the CAL extension below.

| Example | Proposed intent |
| --- | --- |
| `SET_HEAD_PAN,15` | Illustrative head PAN goal; units/signs pending calibration |
| `SET_LEFT_ARM,8` | Illustrative left arm goal; units/signs pending calibration |
| `SET_RIGHT_ARM,-8` | Illustrative right arm goal; units/signs pending calibration |
| `SET_EARS,20,20` | Left/right ear goals |
| `SLEEP` | Request a safe low-activity state, semantics TBD |
| `WAKE` | Request resumption after safety checks, semantics TBD |

These historical numeric examples are not validated physical limits. Old `SET_HEAD` PAN/TILT and `SET_BODY` proposals belonged to the superseded gimbal variant and are not active.

## Extensión manual CAL

`V2,CAL,<HEAD_PAN|LEFT_ARM|RIGHT_ARM>,<1000..2000>` solicita un pulso entero de
cuatro dígitos en microsegundos. Solo está habilitado en el build de calibración,
en READY tras HB y ARM. Conserva las respuestas ACK/NACK V2; READY puede tener
un canal manual activo en este modo. No requiere START ni confirma la mecánica.
Consulta [la secuencia, límites y salida de la prueba](../servo-calibration.md).

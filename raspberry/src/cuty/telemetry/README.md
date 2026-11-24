# Telemetría C.U.T.Y.

`hardware.motion_actions.MotionActionGate.status_snapshot()` expone el modo
activo y la referencia **comandada**. En ROBOT, esta viene de la telemetría STM32;
en SIMULACIÓN, es un objetivo virtual calculado localmente. La
telemetría se valida en el parser UART; el puente limita a 64 los eventos
pendientes aunque el firmware emita datos más rápido que el consumidor.

`TelemetryServer` publica esa instantánea en `GET /api/robot/status`. No
implementa rutas de control, inicia deshabilitado y solo permite enlazar una
dirección loopback. Para habilitarlo desde `cuty --hands-free`, configura
`CUTY_TELEMETRY_ENABLE=1`; `CUTY_TELEMETRY_PORT` elige el puerto y
`CUTY_TELEMETRY_ORIGIN` autoriza un origen CORS exacto. Consulta
`docs/protocol/telemetry.md` para el contrato y la integración con el dashboard.

Sin un ejecutor físico habilitado, la respuesta indica enlace offline y modo
simulación, con referencias virtuales etiquetadas como comandadas. No se exponen
posición medida, batería ni periféricos no observados.

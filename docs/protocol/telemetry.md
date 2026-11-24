# Telemetría V2

El firmware de Black Pill emite `V2,STATE,<estado>,<timestamp_ms>` al cambiar
de estado y `V2,TELEM,<timestamp_ms>,<estado>,<rx_errors>,<dropped_tx>,<head_mU>,<left_mU>,<right_mU>,<uart_status>`
desde su tarea TX. `mU` son milésimas de unidad normalizada; los tres valores
son consignas calculadas por el controlador. El hardware no tiene sensores de
posición, así que no representan ángulos ni posiciones medidas.

El puente Raspberry conserva un máximo de 64 eventos UART pendientes y el
ejecutor mantiene la última instantánea válida. Los contadores permiten ver
errores de recepción y registros descartados por congestión. Una instantánea
se considera reciente durante un segundo; la ausencia o antigüedad de datos no
autoriza movimiento.
Con UART desconectado, `safety_state` pasa a `UNKNOWN` y `last_known_state`
conserva por separado el último estado recibido.

Tras una pérdida de UART, el monitor Raspberry reintenta cada segundo. Al
reconectar no restaura autorización de movimiento: acepta DISARMED, desarma
READY/ACTIVE si reaparecen y no recupera FAULT automáticamente. El movimiento
permanece desautorizado hasta reiniciar el servicio y volver a validar el
estado/perfil. Si el STM32 quedó en FAULT, primero requiere un RESET explícito:
`python -m cuty.hardware.stm32_bridge --port /dev/ttyAMA0 send V2,RESET`.
El objetivo interrumpido nunca se reanuda.

## Endpoint web de solo lectura

El servidor HTTP está deshabilitado por defecto. Para activarlo en el servicio
de voz de Raspberry:

```sh
export CUTY_TELEMETRY_ENABLE=1
export CUTY_TELEMETRY_BIND=127.0.0.1
export CUTY_TELEMETRY_PORT=8765
python -m cuty --hands-free
```

Consulta `http://127.0.0.1:8765/api/robot/status`. Solo existe GET para esta
ruta; no hay comandos de movimiento. El enlace está limitado a loopback. Para
que el dashboard local lo lea, configura `VITE_ROBOT_STATUS_URL` al compilar la
web y `CUTY_TELEMETRY_ORIGIN` con el origen exacto autorizado. No enlaces el
servidor a una interfaz de red: el endpoint no autentica clientes y no debe
exponerse a la LAN o Internet.

Sin `VITE_ROBOT_STATUS_URL`, la web muestra el estado de simulación/offline y
no inventa posiciones. La telemetría de este endpoint describe solo enlace,
estado de seguridad, actividad y consignas; no incluye batería, cámaras,
micrófonos ni medidas físicas.

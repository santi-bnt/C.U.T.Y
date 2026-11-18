import { bi, type Copy } from "./project";
export interface MotionTask {
  id: string;
  name: string;
  priority: string;
  activation: Copy;
  responsibility: Copy;
  io: Copy;
  resources: Copy;
  files: string[];
  status: Copy;
}
export const motionTasks: MotionTask[] = [
  {
    id: "communication",
    name: "CommunicationTask",
    priority: "AboveNormal / 1536 B",
    activation: bi(
      "UART event; bounded batch of 64 bytes",
      "Evento UART; lote limitado a 64 bytes",
    ),
    responsibility: bi(
      "Assemble LF/CRLF frames, reject malformed values, and publish the latest target. Return bounded status/error records.",
      "Reconstruir tramas LF/CRLF, rechazar valores inválidos y publicar el objetivo más reciente. Responder con estados y errores acotados.",
    ),
    io: bi(
      "RX bytes → validated commands / ACK or ERR",
      "Bytes RX → comandos validados / ACK o ERR",
    ),
    resources: bi(
      "RX queue (256 timestamped entries), three target mailboxes (one per joint), command queue (8). Zero-timeout ISR enqueue.",
      "Cola RX (256 entradas con timestamp), tres buzones de objetivos, cola de comandos (8). Encolado ISR sin espera.",
    ),
    files: [
      "stm32/App/communication/uart_protocol.c",
      "stm32/App/rtos/motion_tasks.c",
    ],
    status: bi(
      "Implemented: portable parser. Planned: on-board UART IRQ/DMA integration.",
      "Implemented: parser portable. Planned: integración UART IRQ/DMA en placa.",
    ),
  },
  {
    id: "servo",
    name: "ServoControlTask",
    priority: "High / 1536 B",
    activation: bi("20 ms / 50 Hz proposed", "20 ms / 50 Hz propuestos"),
    responsibility: bi(
      "Own controller state, consume fresh goals, bound velocity and acceleration, and prepare commanded setpoints. Hardware timers must generate the pulses.",
      "Ser dueño del estado, consumir objetivos recientes, limitar velocidad y aceleración y preparar consignas. Los temporizadores hardware deben generar los pulsos.",
    ),
    io: bi(
      "Latest normalized target → commanded position (never measured position)",
      "Último objetivo normalizado → posición comandada (nunca medida)",
    ),
    resources: bi(
      "Target mailbox; absolute osDelayUntil deadline; telemetry queue (1)",
      "Buzón de objetivos; plazo absoluto osDelayUntil; cola de telemetría (1)",
    ),
    files: [
      "stm32/App/control/body_control.c",
      "stm32/App/servos/servo.c",
      "stm32/App/rtos/motion_tasks.c",
    ],
    status: bi(
      "Implemented: portable setpoint filter and pulse conversion. Hardware validation pending.",
      "Implemented: filtro de consignas y conversión de pulsos portables. Hardware validation pending.",
    ),
  },
  {
    id: "safety",
    name: "SafetyTask",
    priority: "High1 / 768 B",
    activation: bi(
      "10 ms proposed; heartbeat timeout 500 ms in dry-run",
      "10 ms propuestos; timeout de heartbeat de 500 ms en dry-run",
    ),
    responsibility: bi(
      "Request supervision; the control owner applies DISARMED → READY → ACTIVE or latched FAULT. Recovery requires RESET, a new heartbeat and explicit arming.",
      "Solicitar supervisión; el dueño del control aplica DISARMED → READY → ACTIVE o FAULT enclavado. Recuperar exige RESET, nuevo heartbeat y armado explícito.",
    ),
    io: bi(
      "Heartbeat age / invalid commands → fault and output policy",
      "Antigüedad del heartbeat / comandos inválidos → fallo y política de salida",
    ),
    resources: bi(
      "Task notification; no concurrent writes to controller or PWM",
      "Notificación de tarea; sin escrituras simultáneas al controlador ni PWM",
    ),
    files: ["stm32/App/safety/safety.c", "stm32/App/rtos/motion_tasks.c"],
    status: bi(
      "Implemented: portable state logic. Planned: watchdog and physical safe-state validation.",
      "Implemented: lógica de estados portable. Planned: watchdog y validación del estado físico seguro.",
    ),
  },
  {
    id: "diagnostics",
    name: "DiagnosticsTask",
    priority: "Low / 1024 B",
    activation: bi(
      "200 ms / at most 5 Hz proposed",
      "200 ms / máximo 5 Hz propuestos",
    ),
    responsibility: bi(
      "Read a consistent snapshot; report goals, commanded positions, state and counters without blocking control. Measured positions remain unavailable.",
      "Leer una instantánea consistente; reportar objetivos, posiciones comandadas, estado y contadores sin bloquear el control. Las posiciones medidas siguen sin estar disponibles.",
    ),
    io: bi(
      "Snapshot → bounded telemetry via CommunicationTask",
      "Instantánea → telemetría acotada por CommunicationTask",
    ),
    resources: bi(
      "Single-slot snapshot and TX queues; drop on congestion",
      "Colas de instantáneas y TX de una entrada; descarte por congestión",
    ),
    files: ["stm32/App/rtos/motion_tasks.c"],
    status: bi(
      "Planned: board transport, task timing and stack/heap measurements. No live telemetry.",
      "Planned: transporte en placa, tiempos de tareas y mediciones de stack/heap. Sin telemetría en vivo.",
    ),
  },
  {
    id: "imu",
    name: "IMUTask",
    priority: "TBD",
    activation: bi("Future; sensor-dependent", "Futura; depende del sensor"),
    responsibility: bi(
      "Reserve a timestamped, calibrated sensor interface. No IMU PID until sensor, axes and mechanics are defined.",
      "Reservar una interfaz de sensor con timestamp y calibración. Sin PID IMU hasta definir sensor, ejes y mecánica.",
    ),
    io: bi(
      "Future sensor → calibrated sample",
      "Sensor futuro → muestra calibrada",
    ),
    resources: bi(
      "Planned only; no task allocated",
      "Sólo planeado; sin tarea creada",
    ),
    files: ["stm32/App/imu/imu.h"],
    status: bi(
      "Planned: interface declaration only.",
      "Planned: sólo declaración de interfaz.",
    ),
  },
];
export const motionSteps = [
  bi(
    "Raspberry generates PAN +0.35 in normalized demo units.",
    "Raspberry genera PAN +0.35 en unidades normalizadas de demostración.",
  ),
  bi(
    "UART delivers V2,TARGET,HEAD_PAN,350 followed by LF.",
    "UART entrega V2,TARGET,HEAD_PAN,350 seguido de LF.",
  ),
  bi(
    "CommunicationTask validates the frame and range.",
    "CommunicationTask valida la trama y el rango.",
  ),
  bi(
      "The joint's single-slot mailbox replaces its obsolete goal.",
      "El buzón de la articulación reemplaza sus objetivos obsoletos.",
  ),
  bi(
    "ServoControlTask computes a velocity- and acceleration-limited transition.",
    "ServoControlTask calcula una transición limitada en velocidad y aceleración.",
  ),
  bi(
    "TIM4 would latch the PAN pulse width. No hardware output occurs here.",
    "TIM4 aplicaría el ancho de pulso PAN. Aquí no se genera salida física.",
  ),
  bi(
    "DiagnosticsTask returns commanded-position telemetry, not a measurement.",
    "DiagnosticsTask devuelve telemetría de posición comandada, no una medición.",
  ),
  bi(
    "Heartbeat is lost: after the illustrative 500 ms timeout, ACTIVE → FAULT; freeze the commanded setpoint, never auto-center. Physical policy remains unverified.",
    "Se pierde el heartbeat: tras el timeout ilustrativo de 500 ms, ACTIVE → FAULT; congelar la consigna, nunca centrar automáticamente. La política física aún no está validada.",
  ),
];

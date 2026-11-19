import { ArrowRight, ArrowUpRight } from "lucide-react";
import { motionStepTasks, motionTasks, type MotionTask } from "../data/motionControl";
import { bi, source, type Copy } from "../data/project";

type Translator = (copy: Copy) => string;
type Props = {
  step: number;
  selectedTask: string | null;
  onSelectTask: (taskId: string) => void;
  t: Translator;
};

const taskPaths: Record<string, string[]> = {
  communication: [
    "pi-goals",
    "uart-entry",
    "pi-chain",
    "communication",
    "queues",
    "uart-to-comm",
    "comm-queue",
  ],
  servo: [
    "queues",
    "servo-control",
    "fir",
    "trajectory",
    "hardware-timer",
    "head",
    "left",
    "right",
    "queue-servo",
    "servo-fir",
    "fir-trajectory",
    "servo-trajectory",
    "trajectory-pwm",
    "pwm-actuators",
  ],
  safety: ["safety", "servo-control", "safety-notify"],
  diagnostics: [
    "servo-control",
    "diagnostics",
    "telemetry",
    "snapshot-diagnostics",
    "diagnostics-telemetry",
  ],
};

const stepPaths = [
  ["pi-track", "pi-process", "pi-goals", "pi-chain"],
  ["pi-goals", "pi-chain", "uart-entry", "uart-to-comm"],
  ["uart-entry", "pi-chain", "communication", "uart-to-comm"],
  ["communication", "queues", "comm-queue"],
  [
    "queues",
    "servo-control",
    "fir",
    "trajectory",
    "queue-servo",
    "servo-fir",
    "fir-trajectory",
    "servo-trajectory",
  ],
  ["trajectory", "hardware-timer", "head", "trajectory-pwm", "pwm-actuators"],
  ["servo-control", "diagnostics", "telemetry", "snapshot-diagnostics", "diagnostics-telemetry"],
  ["safety", "servo-control", "safety-notify"],
];

export default function EmbeddedArchitecture({
  step,
  selectedTask,
  onSelectTask,
  t,
}: Props) {
  const activeTask = motionStepTasks[step] ?? null;
  const focusTask = selectedTask ?? activeTask;
  const relatedPaths = focusTask ? taskPaths[focusTask] : stepPaths[step];
  const related = (id: string) => relatedPaths?.includes(id) ?? false;
  const hasFocus = Boolean(focusTask) || step > 0;
  const active = (id: string) => stepPaths[step]?.includes(id) ?? false;
  const task = focusTask
    ? motionTasks.find((entry) => entry.id === focusTask) ?? null
    : null;

  return (
    <>
      <div
        className="mc-architecture-grid"
        data-has-focus={hasFocus}
        role="group"
        aria-label={t(
          bi(
            "Interactive embedded systems architecture",
            "Arquitectura interactiva de sistemas embebidos",
          ),
        )}
      >
        <section className="mc-architecture-area mc-pi-area" aria-labelledby="mc-pi-heading">
          <AreaHeading number="01" title="Raspberry Pi 5" id="mc-pi-heading" />
          <div className="mc-pi-stack">
            <SignalNode id="pi-track" related={related("pi-track")} active={active("pi-track")} title="FaceTracker" />
            <Wire id="pi-chain" related={related("pi-chain")} active={active("pi-chain")} vertical />
            <SignalNode
              id="pi-process"
              related={related("pi-process")}
              active={active("pi-process")}
              title={t(bi("Visual processing", "Procesamiento visual"))}
              note="Gemini Live"
            />
            <Wire id="pi-chain" related={related("pi-chain")} active={active("pi-chain")} vertical />
            <SignalNode
              id="pi-goals"
              related={related("pi-goals")}
              active={active("pi-goals")}
              title={t(bi("Movement goals", "Objetivos de movimiento"))}
            />
          </div>
        </section>

        <Wire id="pi-chain" related={related("pi-chain")} active={active("pi-chain")} label="UART / V2" className="mc-inter-area-wire" />

        <section className="mc-architecture-area mc-rtos-area" aria-labelledby="mc-rtos-heading">
          <AreaHeading
            number="02"
            title="STM32F401 + FreeRTOS"
            id="mc-rtos-heading"
            note={t(bi("Portable C · preliminary CMSIS-RTOS2 dry-run", "C portable · dry-run CMSIS-RTOS2 preliminar"))}
          />
          <div className="mc-main-pipeline" aria-label={t(bi("UART receive to hardware timer output", "Recepción UART hasta salida de temporizador"))}>
            <SignalNode id="uart-entry" related={related("uart-entry")} active={active("uart-entry")} title="UART RX" note="V2 target" compact />
            <Wire id="uart-to-comm" related={related("uart-to-comm")} active={active("uart-to-comm")} />
            <TaskNode taskId="communication" related={related("communication")} active={active("communication")} selected={selectedTask === "communication"} onSelect={onSelectTask} t={t} />
            <Wire id="comm-queue" related={related("comm-queue")} active={active("comm-queue")} />
            <SignalNode id="queues" related={related("queues")} active={active("queues")} title={t(bi("3 goal queues", "3 colas de objetivos"))} note={t(bi("one per joint", "una por eje"))} compact />
            <Wire id="queue-servo" related={related("queue-servo")} active={active("queue-servo")} />
            <TaskNode taskId="servo" related={related("servo-control")} active={active("servo-control")} selected={selectedTask === "servo"} onSelect={onSelectTask} t={t} />
            <span className="mc-branch-point" aria-hidden="true" data-related={related("servo-control")} data-active={active("servo-control")} />
            <Wire id="servo-fir" related={related("servo-fir")} active={active("servo-fir")} />
            <SignalNode id="fir" related={related("fir")} active={active("fir")} title="FIR low-pass" note="HEAD_PAN only" compact />
            <Wire id="fir-trajectory" related={related("fir-trajectory")} active={active("fir-trajectory")} />
            <SignalNode id="trajectory" related={related("trajectory")} active={active("trajectory")} title={t(bi("Trajectory control", "Control de trayectoria"))} note={t(bi("arms bypass FIR", "brazos sin FIR"))} compact />
            <Wire id="trajectory-pwm" related={related("trajectory-pwm")} active={active("trajectory-pwm")} />
            <SignalNode id="hardware-timer" related={related("hardware-timer")} active={active("hardware-timer")} title={t(bi("Hardware timer", "Timer de hardware"))} note="TIM4 CH1–3" compact />
          </div>
          <div className="mc-arm-bypass" data-related={related("servo-trajectory")} data-active={active("servo-trajectory")}>
            <span className="mc-branch-line" aria-hidden="true" />
            <span>{t(bi("LEFT_ARM + RIGHT_ARM: trajectory limits, bypass HEAD_PAN FIR", "LEFT_ARM + RIGHT_ARM: límites de trayectoria; omiten FIR de HEAD_PAN"))}</span>
          </div>
          <div className="mc-parallel-tasks">
            <div className="mc-parallel-task mc-safety-lane">
              <TaskNode taskId="safety" related={related("safety")} active={active("safety")} selected={selectedTask === "safety"} onSelect={onSelectTask} t={t} />
              <Wire id="safety-notify" related={related("safety-notify")} active={active("safety-notify")} label={t(bi("10 ms notification → control owner", "Notificación 10 ms → dueño del control"))} />
              <span className="mc-lane-target" data-related={related("servo-control")} data-active={active("servo-control")}>ServoControlTask</span>
            </div>
            <div className="mc-parallel-task mc-diagnostics-lane">
              <span className="mc-lane-target" data-related={related("servo-control")} data-active={active("servo-control")}>{t(bi("Controller snapshot", "Instantánea del control"))}</span>
              <Wire id="snapshot-diagnostics" related={related("snapshot-diagnostics")} active={active("snapshot-diagnostics")} />
              <TaskNode taskId="diagnostics" related={related("diagnostics")} active={active("diagnostics")} selected={selectedTask === "diagnostics"} onSelect={onSelectTask} t={t} />
              <Wire id="diagnostics-telemetry" related={related("diagnostics-telemetry")} active={active("diagnostics-telemetry")} />
              <SignalNode id="telemetry" related={related("telemetry")} active={active("telemetry")} title={t(bi("Telemetry queue", "Cola de telemetría"))} note={t(bi("TX adapter pending", "Adaptador TX pendiente"))} compact />
            </div>
          </div>
          <p className="mc-pwm-note">{t(bi("FreeRTOS prepares setpoints; timer peripherals generate PWM independently. UART and PWM are not hardware-validated.", "FreeRTOS prepara consignas; los periféricos timer generan PWM de forma independiente. UART y PWM no están validados en hardware."))}</p>
        </section>

        <Wire id="pwm-actuators" related={related("pwm-actuators")} active={active("pwm-actuators")} label="TIM4 CH1–3" className="mc-output-wire" />

        <section className="mc-architecture-area mc-actuator-area" aria-labelledby="mc-actuator-heading">
          <AreaHeading number="03" title={t(bi("Actuator outputs", "Salidas a actuadores"))} id="mc-actuator-heading" note={t(bi("Physical movement unconfirmed", "Movimiento físico sin confirmar"))} />
          <div className="mc-actuator-outputs">
            <Actuator id="head" active={active("head")} related={related("head")} name="HEAD_PAN" connector="J7" />
            <Actuator id="left" active={active("left")} related={related("left")} name="LEFT_ARM" connector="J8" />
            <Actuator id="right" active={active("right")} related={related("right")} name="RIGHT_ARM" connector="J9" />
          </div>
          <p className="mc-reserved-note">{t(bi("5 carrier channels · J10 / J11 reserved", "5 canales en carrier · J10 / J11 reservados"))}</p>
        </section>
      </div>

      <TaskDetails task={task} t={t} />
      {!task && (
        <aside className="mc-task-details mc-task-prompt" aria-live="polite">
          <span className="eyebrow">{t(bi("TASK INSPECTOR", "INSPECTOR DE TAREAS"))}</span>
          <p>{t(bi("Select CommunicationTask, ServoControlTask, SafetyTask or DiagnosticsTask in the diagram to inspect its role, priority, period and implementation status.", "Selecciona CommunicationTask, ServoControlTask, SafetyTask o DiagnosticsTask en el diagrama para consultar su función, prioridad, periodo y estado."))}</p>
        </aside>
      )}
    </>
  );
}

function AreaHeading({ number, title, id, note }: { number: string; title: string; id: string; note?: string }) {
  return (
    <header className="mc-area-heading">
      <span className="eyebrow">{number} /</span>
      <h3 id={id}>{title}</h3>
      {note && <p>{note}</p>}
    </header>
  );
}

function SignalNode({ id, related, active, title, note, compact = false }: { id: string; related: boolean; active: boolean; title: string; note?: string; compact?: boolean }) {
  return (
    <div className={`mc-signal-node${compact ? " is-compact" : ""}`} data-node={id} data-related={related} data-active={active}>
      <span className="mc-connection-dot" aria-hidden="true" />
      <strong>{title}</strong>
      {note && <span>{note}</span>}
    </div>
  );
}

function TaskNode({ taskId, related, active, selected, onSelect, t }: { taskId: string; related: boolean; active: boolean; selected: boolean; onSelect: (taskId: string) => void; t: Translator }) {
  const task = motionTasks.find((item) => item.id === taskId)!;
  return (
    <button
      type="button"
      className="mc-task-node"
      data-node={taskId === "servo" ? "servo-control" : taskId}
      data-related={related}
      data-active={active}
      data-selected={selected}
      aria-pressed={selected}
      aria-label={`${task.name}: ${t(task.summary)}`}
      onClick={() => onSelect(taskId)}
    >
      <span className="mc-connection-dot" aria-hidden="true" />
      <strong>
        {task.name.replace(/Task$/, "")}
        <wbr />Task
      </strong>
    </button>
  );
}

function Wire({ id, related, active, vertical = false, label, className = "" }: { id: string; related: boolean; active: boolean; vertical?: boolean; label?: string; className?: string }) {
  return (
      <div className={`mc-wire${vertical ? " is-vertical" : ""} ${className}`} data-wire={id} data-related={related} data-active={active}>
      <span aria-hidden="true" />
      {label && <small aria-hidden="true">{label}</small>}
    </div>
  );
}

function Actuator({ id, active, related, name, connector }: { id: string; active: boolean; related: boolean; name: string; connector: string }) {
  return (
    <div className="mc-actuator-output" data-node={id} data-related={related} data-active={active}>
      <span className="mc-terminal" aria-hidden="true" />
      <strong>{name}</strong>
      <code>{connector} · MG996R</code>
    </div>
  );
}

function TaskDetails({ task, t }: { task: MotionTask | null; t: Translator }) {
  if (!task) return null;
  return (
    <aside className="mc-task-details" aria-live="polite" aria-label={t(bi("Selected task details", "Detalles de la tarea seleccionada"))}>
      <div className="mc-task-detail-main">
        <span className="eyebrow">{t(bi("SELECTED TASK", "TAREA SELECCIONADA"))}</span>
        <h4>{task.name}</h4>
        <p>{t(task.summary)}</p>
      </div>
      <dl>
        <div><dt>{t(bi("Priority / stack", "Prioridad / pila"))}</dt><dd>{task.priority}</dd></div>
        <div><dt>{t(bi("Activation / period", "Activación / periodo"))}</dt><dd>{t(task.activation)}</dd></div>
        <div><dt>{t(bi("Implementation status", "Estado de implementación"))}</dt><dd>{t(task.status)}</dd></div>
      </dl>
      <details className="mc-task-advanced">
        <summary>{t(bi("I/O, resources & source", "E/S, recursos y código"))}<ArrowUpRight size={14} aria-hidden="true" /></summary>
        <p><strong>{t(bi("Function", "Función"))}</strong>{t(task.responsibility)}</p>
        <p><strong>{t(bi("Inputs → outputs", "Entradas → salidas"))}</strong>{t(task.io)}</p>
        <p><strong>{t(bi("Resources", "Recursos"))}</strong>{t(task.resources)}</p>
        {task.files.map((path) => <a key={path} href={source(path)} target="_blank" rel="noreferrer">{path}<ArrowRight size={13} aria-hidden="true" /></a>)}
      </details>
    </aside>
  );
}


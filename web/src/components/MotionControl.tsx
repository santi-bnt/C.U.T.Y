import { useEffect, useState } from "react";
import { ArrowDown, ArrowRight, ChevronDown, RotateCcw } from "lucide-react";
import {
  motionSteps,
  motionStepLabels,
  motionStepNodes,
  motionStepTasks,
  motionTasks,
  type MotionTask,
} from "../data/motionControl";
import { bi, source } from "../data/project";
import { useLocale } from "../state/Locale";
import { useMedia } from "../state/useMedia";
import "./motion-control.css";

type NodeId = "raspberry" | "stm32" | "servos";

export default function MotionControl() {
  const { t } = useLocale();
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedNode, setSelectedNode] = useState<NodeId>("stm32");
  const [selectedTask, setSelectedTask] = useState("servo");

  useEffect(() => {
    if (!playing || reduced) return;
    const timer = window.setTimeout(() => {
      if (step >= motionSteps.length - 1) setPlaying(false);
      else setStep((current) => current + 1);
    }, 1800);
    return () => window.clearTimeout(timer);
  }, [playing, reduced, step]);

  const activeNode = motionStepNodes[step] as NodeId;
  const activeTask = motionStepTasks[step];
  const task =
    motionTasks.find((item) => item.id === selectedTask) ?? motionTasks[0];
  const setStage = (next: number) => {
    setPlaying(false);
    setStep(Math.max(0, Math.min(motionSteps.length - 1, next)));
  };

  return (
    <section
      id="motion-control"
      className="motion-control paper"
      aria-labelledby="motion-title"
    >
      <header className="mc-intro">
        <div>
          <span className="eyebrow">08 / REAL-TIME ARCHITECTURE</span>
          <h2 id="motion-title">FreeRTOS / Motion Control</h2>
          <p className="mc-subtitle">
            {t(
              bi(
                "How C.U.T.Y. translates perception into controlled movement.",
                "Cómo C.U.T.Y. transforma la percepción en movimiento controlado.",
              ),
            )}
          </p>
          <p className="mc-intro-copy">
            {t(
              bi(
                "The Raspberry Pi processes vision and AI. The STM32F401 is designed to handle real-time movement, signal filtering and local safety.",
                "La Raspberry Pi procesa visión e IA. El STM32F401 está diseñado para encargarse del movimiento en tiempo real, el filtrado de señal y la seguridad local.",
              ),
            )}
          </p>
        </div>
        <div className="mc-release-state" role="note">
          <span className="mc-state-dot" aria-hidden="true" />
          {t(
            bi(
              "In development — Hardware integration pending",
              "En desarrollo — Integración de hardware pendiente",
            ),
          )}
        </div>
      </header>

      <ul
        className="mc-status-strip"
        aria-label={t(bi("Implementation status", "Estado de implementación"))}
      >
        <li>
          <strong>C logic</strong>
          <span>{t(bi("implemented", "implementada"))}</span>
        </li>
        <li>
          <strong>CMSIS-RTOS2</strong>
          <span>{t(bi("preliminary dry-run", "dry-run preliminar"))}</span>
        </li>
        <li>
          <strong>UART / PWM</strong>
          <span>{t(bi("not validated", "sin validar"))}</span>
        </li>
        <li>
          <strong>{t(bi("Physical motion", "Movimiento físico"))}</strong>
          <span>{t(bi("unconfirmed", "sin confirmar"))}</span>
        </li>
      </ul>

      <div className="mc-diagram-shell">
        <div className="mc-diagram-heading">
          <div>
            <span className="eyebrow">SIGNAL PATH / 01—03</span>
            <h3>
              {t(bi("From goal to actuator", "Del objetivo al actuador"))}
            </h3>
          </div>
          <span className="mc-diagram-note">
            {t(
              bi(
                "Planned architecture · local visualization",
                "Arquitectura propuesta · visualización local",
              ),
            )}
          </span>
        </div>

        <div
          className="mc-diagram"
          aria-label={t(
            bi(
              "Selectable motion-control signal path",
              "Ruta seleccionable de control de movimiento",
            ),
          )}
        >
          <DiagramNode
            id="raspberry"
            selected={selectedNode === "raspberry"}
            active={activeNode === "raspberry"}
            onSelect={() => setSelectedNode("raspberry")}
            number="01"
            title="Raspberry Pi 5"
            meta={t(bi("PERCEPTION / PLANNING", "PERCEPCIÓN / PLANIFICACIÓN"))}
            lines={[
              "FaceTracker",
              "Gemini Live",
              t(bi("Movement goals", "Objetivos de movimiento")),
            ]}
          />
          <DiagramLink
            active={step === 1}
            label="UART"
            detail={t(bi("targets / status", "objetivos / estado"))}
          />
          <DiagramNode
            id="stm32"
            selected={selectedNode === "stm32"}
            active={activeNode === "stm32"}
            onSelect={() => setSelectedNode("stm32")}
            number="02"
            title="STM32F401 + FreeRTOS"
            meta={t(
              bi(
                "REAL-TIME CONTROL / IN DEVELOPMENT",
                "CONTROL EN TIEMPO REAL / EN DESARROLLO",
              ),
            )}
            activeLine={
              activeTask === "communication"
                ? 0
                : activeTask === "servo"
                  ? 1
                  : activeTask
                    ? 2
                    : undefined
            }
            lines={[
              "CommunicationTask → FreeRTOS queues (3 targets)",
              "ServoControlTask → FIR low-pass · HEAD_PAN",
              "SafetyTask · DiagnosticsTask",
            ]}
          />
          <DiagramLink
            active={step === 5}
            label={t(bi("Timer outputs", "Salidas de temporizador"))}
            detail={t(bi("not validated", "sin validar"))}
          />
          <DiagramNode
            id="servos"
            selected={selectedNode === "servos"}
            active={activeNode === "servos"}
            onSelect={() => setSelectedNode("servos")}
            number="03"
            title={t(bi("3 × MG996R", "3 × MG996R"))}
            meta={t(
              bi(
                "PHYSICAL OUTPUTS / UNCONFIRMED",
                "SALIDAS FÍSICAS / SIN CONFIRMAR",
              ),
            )}
            lines={["HEAD_PAN · J7", "LEFT_ARM · J8", "RIGHT_ARM · J9"]}
          />
        </div>
        <p className="mc-carrier-note">
          {t(
            bi(
              "Carrier has five servo channels; J10 and J11 stay reserved. The web simulation sends no commands to hardware.",
              "La carrier tiene cinco canales para servos; J10 y J11 quedan reservados. La simulación web no envía comandos al hardware.",
            ),
          )}
        </p>
      </div>

      <div className="mc-task-section">
        <div className="mc-section-heading">
          <span className="eyebrow">02 / TASK EXPLORER</span>
          <h3>
            {t(
              bi(
                "Four tasks. One control owner.",
                "Cuatro tareas. Un único dueño del control.",
              ),
            )}
          </h3>
          <p>
            {t(
              bi(
                "Select a task to inspect its inputs, resources and implementation status.",
                "Selecciona una tarea para ver sus entradas, recursos y estado de implementación.",
              ),
            )}
          </p>
        </div>
        <div className="mc-task-layout">
          <div
            className="mc-task-grid"
            role="group"
            aria-label={t(bi("FreeRTOS tasks", "Tareas FreeRTOS"))}
          >
            {motionTasks
              .filter((item) => item.id !== "imu")
              .map((item) => (
                <TaskCard
                  key={item.id}
                  task={item}
                  selected={task.id === item.id}
                  active={activeTask === item.id}
                  onSelect={() => setSelectedTask(item.id)}
                  t={t}
                />
              ))}
          </div>
          <TaskDetails key={task.id} task={task} t={t} />
        </div>
        <details className="mc-future">
          <summary>
            <span>{t(bi("Future extensions", "Extensiones futuras"))}</span>
            <span className="mc-future-label">
              {t(
                bi(
                  "Not part of active motion control",
                  "Fuera del control de movimiento activo",
                ),
              )}
            </span>
            <ChevronDown size={18} aria-hidden="true" />
          </summary>
          <div className="mc-future-content">
            <strong>
              IMUTask · {t(bi("not implemented", "no implementada"))}
            </strong>
            <p>
              {t(motionTasks.find((item) => item.id === "imu")!.responsibility)}
            </p>
            <a
              href={source("stm32/App/imu/imu.h")}
              target="_blank"
              rel="noreferrer"
            >
              stm32/App/imu/imu.h
            </a>
          </div>
        </details>
      </div>

      <div className="mc-lower-grid">
        <section
          className="mc-simulation"
          aria-labelledby="mc-simulation-title"
        >
          <div className="mc-section-heading">
            <span className="eyebrow">03 / LOCAL SIMULATION</span>
            <h3 id="mc-simulation-title">
              {t(bi("Follow a PAN goal", "Sigue un objetivo PAN"))}
            </h3>
            <p>
              {t(
                bi(
                  "Illustrative dry-run. Stages explain the planned flow; no robot data is read or sent.",
                  "Dry-run ilustrativo. Los pasos explican el flujo propuesto; no se lee ni envía información al robot.",
                ),
              )}
            </p>
          </div>
          <div className="mc-sim-progress">
            <span>
              {t(
                bi(
                  `Step ${step + 1} of ${motionSteps.length}`,
                  `Paso ${step + 1} de ${motionSteps.length}`,
                ),
              )}
            </span>
            <span className="mc-progress-track" aria-hidden="true">
              <span
                style={{ width: `${((step + 1) / motionSteps.length) * 100}%` }}
              />
            </span>
          </div>
          <article key={step} className="mc-step-card" aria-live="polite">
            <span className="eyebrow">{t(motionStepLabels[step])}</span>
            <h4>{t(motionSteps[step])}</h4>
            {step === motionSteps.length - 1 && (
              <p className="mc-fault-note">
                {t(
                  bi(
                    "Fault is latched. A heartbeat alone cannot recover motion.",
                    "La falla queda enclavada. El heartbeat por sí solo no recupera el movimiento.",
                  ),
                )}
              </p>
            )}
          </article>
          <div
            className="mc-sim-controls"
            role="group"
            aria-label={t(bi("Simulation controls", "Controles de simulación"))}
          >
            <button
              type="button"
              onClick={() => setStage(step - 1)}
              disabled={step === 0}
            >
              <ArrowDown
                className="mc-previous-icon"
                size={16}
                aria-hidden="true"
              />
              {t(bi("Previous", "Anterior"))}
            </button>
            {!reduced && (
              <button
                type="button"
                className="mc-play-button"
                onClick={() => {
                  if (!playing && step === motionSteps.length - 1) setStep(0);
                  setPlaying((value) => !value);
                }}
              >
                {playing
                  ? t(bi("Pause", "Pausar"))
                  : t(bi("Play", "Reproducir"))}
              </button>
            )}
            <button
              type="button"
              onClick={() => setStage(step + 1)}
              disabled={step === motionSteps.length - 1}
            >
              {t(bi("Next", "Siguiente"))}
              <ArrowRight size={16} aria-hidden="true" />
            </button>
            <button
              type="button"
              className="mc-reset-button"
              onClick={() => setStage(0)}
            >
              <RotateCcw size={15} aria-hidden="true" />
              {t(bi("Reset", "Reiniciar"))}
            </button>
          </div>
          {reduced && (
            <p className="mc-reduced-note">
              {t(
                bi(
                  "Autoplay is off while reduced motion is enabled. Use Previous and Next to explore.",
                  "La reproducción automática está desactivada con movimiento reducido. Usa Anterior y Siguiente para explorar.",
                ),
              )}
            </p>
          )}
          <button
            type="button"
            className="mc-heartbeat-button"
            onClick={() => setStage(motionSteps.length - 1)}
          >
            {t(bi("Simulate heartbeat loss", "Simular pérdida de heartbeat"))}
            <ArrowRight size={15} aria-hidden="true" />
          </button>
          <p className="mc-sim-status" role="status">
            {step === motionSteps.length - 1
              ? t(
                  bi(
                    "Simulated · ACTIVE → FAULT · no data is transmitted.",
                    "Simulado · ACTIVE → FAULT · no se transmiten datos.",
                  ),
                )
              : t(
                  bi(
                    `Simulated · Step ${step + 1} of ${motionSteps.length} · no data is transmitted.`,
                    `Simulado · Paso ${step + 1} de ${motionSteps.length} · no se transmiten datos.`,
                  ),
                )}
          </p>
          <details className="mc-sequence">
            <summary>
              {t(bi("Review all eight stages", "Revisar los ocho pasos"))}
              <ChevronDown size={17} aria-hidden="true" />
            </summary>
            <ol>
              {motionSteps.map((copy, index) => (
                <li
                  key={index}
                  aria-current={step === index ? "step" : undefined}
                >
                  <button type="button" onClick={() => setStage(index)}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    {t(copy)}
                  </button>
                </li>
              ))}
            </ol>
          </details>
        </section>

        <section className="mc-safety" aria-labelledby="mc-safety-title">
          <div className="mc-section-heading">
            <span className="eyebrow">04 / SAFETY STATES</span>
            <h3 id="mc-safety-title">
              {t(
                bi(
                  "Explicit arming. Latched fault.",
                  "Armado explícito. Falla enclavada.",
                ),
              )}
            </h3>
          </div>
          <div
            className="mc-state-diagram"
            aria-label={t(
              bi(
                "Illustrative control state machine",
                "Máquina de estados ilustrativa",
              ),
            )}
          >
            <div className="mc-state-row">
              {(["DISARMED", "READY", "ACTIVE"] as const).map(
                (state, index) => (
                  <span className="mc-state-step" key={state}>
                    {index > 0 && <ArrowRight size={17} aria-hidden="true" />}
                    <strong
                      data-current={
                        step === 7 && state === "ACTIVE" ? "true" : undefined
                      }
                    >
                      {state}
                    </strong>
                  </span>
                ),
              )}
            </div>
            <div className="mc-fault-branch">
              <ArrowDown size={17} aria-hidden="true" />
              <strong data-current={step === 7 ? "true" : undefined}>
                FAULT
              </strong>
            </div>
          </div>
          <p className="mc-safety-copy">
            {t(
              bi(
                "Heartbeat loss or invalid control input can latch FAULT. Recovery requires RESET, a fresh heartbeat, then explicit ARM and START. Heartbeat alone does not restart motion.",
                "La pérdida de heartbeat o una entrada de control inválida puede enclavar FAULT. Para recuperar se requiere RESET, un heartbeat reciente y después ARM y START explícitos. El heartbeat por sí solo no reinicia el movimiento.",
              ),
            )}
          </p>
          <p className="mc-safety-caveat">
            {t(
              bi(
                "Illustrative software state flow only — not physically validated.",
                "Flujo ilustrativo de software — sin validación física.",
              ),
            )}
          </p>
        </section>
      </div>

      <details className="mc-why">
        <summary>
          {t(
            bi(
              "Why FreeRTOS alongside Linux?",
              "¿Por qué FreeRTOS junto a Linux?",
            ),
          )}
          <ChevronDown size={18} aria-hidden="true" />
        </summary>
        <div>
          <p>
            {t(
              bi(
                "Linux keeps vision, voice and planning flexible. A dedicated microcontroller can isolate periodic control and local safety supervision from those workloads. FreeRTOS schedules tasks; timer peripherals generate PWM independently. Determinism still requires measured execution times, interrupt budgets and hardware validation.",
                "Linux mantiene flexibles la visión, la voz y la planificación. Un microcontrolador dedicado puede aislar el control periódico y la supervisión de seguridad local de esas cargas. FreeRTOS organiza las tareas; los periféricos timer generan PWM de forma independiente. El determinismo aún requiere medir tiempos de ejecución, presupuestos de interrupciones y validar el hardware.",
              ),
            )}
          </p>
          <a
            href={source("docs/freertos-motion-control.md")}
            target="_blank"
            rel="noreferrer"
          >
            {t(
              bi(
                "Architecture, tests and hardware checklist",
                "Arquitectura, pruebas y lista de hardware",
              ),
            )}
            <ArrowRight size={15} aria-hidden="true" />
          </a>
        </div>
      </details>
    </section>
  );
}

function DiagramNode({
  id,
  selected,
  active,
  onSelect,
  number,
  title,
  meta,
  lines,
  activeLine,
}: {
  id: NodeId;
  selected: boolean;
  active: boolean;
  onSelect: () => void;
  number: string;
  title: string;
  meta: string;
  lines: string[];
  activeLine?: number;
}) {
  return (
    <button
      type="button"
      className="mc-node"
      data-node={id}
      data-selected={selected}
      data-flow-active={active}
      aria-pressed={selected}
      onClick={onSelect}
    >
      <span className="mc-node-meta">
        <span>{number} /</span>
        {meta}
      </span>
      <strong>{title}</strong>
      <span className="mc-node-lines">
        {lines.map((line, index) => (
          <span key={line} data-active={activeLine === index}>
            {line}
          </span>
        ))}
      </span>
    </button>
  );
}

function DiagramLink({
  active,
  label,
  detail,
}: {
  active: boolean;
  label: string;
  detail: string;
}) {
  return (
    <div className="mc-connection" data-flow-active={active}>
      <ArrowRight size={22} aria-hidden="true" />
      <strong>{label}</strong>
      <span>{detail}</span>
    </div>
  );
}

function TaskCard({
  task,
  selected,
  active,
  onSelect,
  t,
}: {
  task: MotionTask;
  selected: boolean;
  active: boolean;
  onSelect: () => void;
  t: (copy: { en: string; es: string }) => string;
}) {
  return (
    <button
      type="button"
      className="mc-task-card"
      data-selected={selected}
      data-flow-active={active}
      aria-pressed={selected}
      onClick={onSelect}
    >
      <span className="mc-task-card-top">
        <code>{task.name}</code>
        <span>{t(task.implementation)}</span>
      </span>
      <span className="mc-task-summary">{t(task.summary)}</span>
      <span className="mc-task-meta">
        <span>
          <small>{t(bi("Priority", "Prioridad"))}</small>
          <strong>{task.priority.split(" /")[0]}</strong>
        </span>
        <span>
          <small>{t(bi("Runs", "Se activa"))}</small>
          <strong>{t(task.condition)}</strong>
        </span>
      </span>
    </button>
  );
}

function TaskDetails({
  task,
  t,
}: {
  task: MotionTask;
  t: (copy: { en: string; es: string }) => string;
}) {
  return (
    <aside
      className="mc-task-details"
      aria-live="polite"
      aria-label={t(
        bi("Selected task details", "Detalles de la tarea seleccionada"),
      )}
    >
      <span className="eyebrow">
        {t(bi("SELECTED TASK", "TAREA SELECCIONADA"))}
      </span>
      <h4>{task.name}</h4>
      <p className="mc-detail-lead">{t(task.responsibility)}</p>
      <dl>
        <div>
          <dt>
            {t(bi("Priority / stack budget", "Prioridad / memoria de pila"))}
          </dt>
          <dd>{task.priority}</dd>
        </div>
        <div>
          <dt>{t(bi("Activation condition", "Condición de activación"))}</dt>
          <dd>{t(task.activation)}</dd>
        </div>
        <div>
          <dt>{t(bi("Inputs → outputs", "Entradas → salidas"))}</dt>
          <dd>{t(task.io)}</dd>
        </div>
        <div>
          <dt>{t(bi("Queues / resources", "Colas / recursos"))}</dt>
          <dd>{t(task.resources)}</dd>
        </div>
        <div>
          <dt>{t(bi("Implementation status", "Estado de implementación"))}</dt>
          <dd>{t(task.status)}</dd>
        </div>
      </dl>
      <div className="mc-source-links">
        {task.files.map((path) => (
          <a key={path} href={source(path)} target="_blank" rel="noreferrer">
            {path}
            <ArrowRight size={14} aria-hidden="true" />
          </a>
        ))}
      </div>
    </aside>
  );
}

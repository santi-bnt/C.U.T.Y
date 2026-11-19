import { useEffect, useState } from "react";
import { ArrowDown, ArrowRight, ChevronDown, RotateCcw } from "lucide-react";
import {
  motionSteps,
  motionStepLabels,
  motionStepTasks,
  motionTasks,
} from "../data/motionControl";
import { bi, source } from "../data/project";
import { useLocale } from "../state/Locale";
import { useMedia } from "../state/useMedia";
import EmbeddedArchitecture from "./EmbeddedArchitecture";
import "./motion-control.css";

export default function MotionControl() {
  const { t } = useLocale();
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);

  useEffect(() => {
    if (!playing || reduced) return;
    const timer = window.setTimeout(() => {
      if (step >= motionSteps.length - 1) setPlaying(false);
      else {
        const next = step + 1;
        setStep(next);
        setSelectedTask(motionStepTasks[next] ?? null);
      }
    }, 1800);
    return () => window.clearTimeout(timer);
  }, [playing, reduced, step]);

  const setStage = (next: number) => {
    setPlaying(false);
    const bounded = Math.max(0, Math.min(motionSteps.length - 1, next));
    setStep(bounded);
    setSelectedTask(motionStepTasks[bounded] ?? null);
  };
  const selectTask = (taskId: string) => {
    setPlaying(false);
    setSelectedTask(taskId);
    const firstStep = motionStepTasks.findIndex((id) => id === taskId);
    if (firstStep >= 0) setStep(firstStep);
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

      <div className="mc-diagram-heading">
        <div>
          <span className="eyebrow">SIGNAL PATH / 01—03</span>
          <h3>{t(bi("From goal to actuator", "Del objetivo al actuador"))}</h3>
        </div>
        <span className="mc-diagram-note">
          {t(bi("Interactive embedded systems architecture", "Arquitectura interactiva de sistemas embebidos"))}
        </span>
      </div>
      <EmbeddedArchitecture
        step={step}
        selectedTask={selectedTask}
        onSelectTask={selectTask}
        t={t}
      />
      <div className="mc-future-wrap">
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
          <article className="mc-step-card" aria-live="polite">
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
                  if (!playing && step === motionSteps.length - 1) {
                    setStep(0);
                    setSelectedTask(null);
                  }
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

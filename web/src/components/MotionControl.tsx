import { useEffect, useState } from "react";
import { bi, source } from "../data/project";
import { motionSteps, motionTasks } from "../data/motionControl";
import { useLocale } from "../state/Locale";
import { useMedia } from "../state/useMedia";
import "./motion-control.css";

export default function MotionControl() {
  const { t } = useLocale();
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [step, setStep] = useState(-1);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing || reduced) return;
    const timer = window.setTimeout(() => {
      if (step >= motionSteps.length - 1) setPlaying(false);
      else setStep(step + 1);
    }, 1800);
    return () => window.clearTimeout(timer);
  }, [playing, reduced, step]);
  const active =
    step === 2
      ? "communication"
      : step === 4
        ? "servo"
        : step === 6
          ? "diagnostics"
          : step === 7
            ? "safety"
            : "";
  return (
    <section
      id="motion-control"
      className="motion-control ink"
      aria-labelledby="motion-title"
    >
      <div className="motion-heading">
        <span className="eyebrow">08 / REAL-TIME ARCHITECTURE</span>
        <h2 id="motion-title">FreeRTOS / Motion Control</h2>
        <p>
          {t(
            bi(
              "From intention to motion. The Pi decides where to look; the proposed STM32 layer owns timing and local safety.",
              "De la intención al movimiento. La Pi decide hacia dónde mirar; la capa STM32 propuesta se encarga de la temporización y la seguridad local.",
            ),
          )}
        </p>
      </div>
      <p className="motion-notice">
        {t(
          bi(
            "In development · local educational simulation · no robot connection. Portable C logic exists; on-board FreeRTOS, UART and PWM integration remain pending.",
            "En desarrollo · simulación educativa local · sin conexión al robot. Existe lógica C portable; la integración FreeRTOS, UART y PWM en placa sigue pendiente.",
          ),
        )}
      </p>
      <div className="motion-legend">
        <span>
          Implemented — {t(bi("portable C logic", "lógica C portable"))}
        </span>
        <span>Simulated — {t(bi("this diagram", "este diagrama"))}</span>
        <span>
          Planned —{" "}
          {t(bi("board integration / IMU", "integración en placa / IMU"))}
        </span>
        <span>Hardware validation pending</span>
      </div>
      <div
        className="motion-diagram"
        aria-label={t(
          bi("Three-layer command flow", "Flujo de comandos en tres niveles"),
        )}
      >
        <article className="motion-layer" data-active={step === 0}>
          <span className="eyebrow">01 / RASPBERRY PI 5</span>
          <h3>{t(bi("Perceive & plan", "Percibir y planear"))}</h3>
          <p>
            FaceTracker · Gemini Live ·{" "}
            {t(bi("vision → goals → UART", "visión → objetivos → UART"))}
          </p>
          <p>
            {t(
              bi(
                "Head follow remains dry-run. No Raspberry GPIO, display or ReSpeaker changes.",
                "El seguimiento de cabeza sigue en dry-run. Sin cambios a GPIO, pantalla ni ReSpeaker de Raspberry.",
              ),
            )}
          </p>
        </article>
        <Flow
          label={t(
            bi(
              "UART · high-level targets ↓ / status ↑",
              "UART · objetivos de alto nivel ↓ / estado ↑",
            ),
          )}
          active={step === 1}
        />
        <article className="motion-layer">
          <span className="eyebrow">
            02 / STM32F401 + FREERTOS · PLANNED INTEGRATION
          </span>
          <h3>
            {t(
              bi("Validate → queue → control", "Validar → encolar → controlar"),
            )}
          </h3>
          <p className="motion-mailbox" data-active={step === 3}>
            {t(
              bi(
                "CommunicationTask → latest-target queue [1] → ServoControlTask",
                "CommunicationTask → cola del último objetivo [1] → ServoControlTask",
              ),
            )}
          </p>
          <div className="motion-tasks">
            {motionTasks.map((task) => (
              <details
                key={task.id}
                className="motion-task"
                data-active={active === task.id}
              >
                <summary>
                  {task.name}
                  <span aria-hidden="true"> +</span>
                </summary>
                <p>{t(task.responsibility)}</p>
                <dl>
                  <div>
                    <dt>
                      {t(
                        bi(
                          "Priority / stack budget",
                          "Prioridad / presupuesto de stack",
                        ),
                      )}
                    </dt>
                    <dd>{task.priority}</dd>
                  </div>
                  <div>
                    <dt>{t(bi("Activation", "Activación"))}</dt>
                    <dd>{t(task.activation)}</dd>
                  </div>
                  <div>
                    <dt>{t(bi("Inputs → outputs", "Entradas → salidas"))}</dt>
                    <dd>{t(task.io)}</dd>
                  </div>
                  <div>
                    <dt>{t(bi("Resources", "Recursos"))}</dt>
                    <dd>{t(task.resources)}</dd>
                  </div>
                  <div>
                    <dt>{t(bi("Actual status", "Estado real"))}</dt>
                    <dd>{t(task.status)}</dd>
                  </div>
                </dl>
                {task.files.map((path) => (
                  <a
                    className="text-link"
                    key={path}
                    href={source(path)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {path}
                  </a>
                ))}
              </details>
            ))}
          </div>
          <p className="motion-states">DISARMED → READY → ACTIVE → FAULT</p>
          <p>
            {t(
              bi(
                "Boot without output. Fresh heartbeat + explicit ARM and START. A fault stays latched until RESET; heartbeat alone cannot restart motion.",
                "Arranque sin salida. Heartbeat reciente + ARM y START explícitos. Un fallo permanece enclavado hasta RESET; el heartbeat por sí solo no reinicia el movimiento.",
              ),
            )}
          </p>
        </article>
        <Flow
          label={t(
            bi(
              "Commanded pulse widths ↓ / diagnostic snapshots ↑",
              "Anchos de pulso comandados ↓ / instantáneas de diagnóstico ↑",
            ),
          )}
          active={step === 5 || step === 6}
        />
        <article className="motion-layer" data-active={step === 5}>
          <span className="eyebrow">
            03 /{" "}
            {t(
              bi("PHYSICAL HARDWARE · PENDING", "HARDWARE FÍSICO · PENDIENTE"),
            )}
          </span>
          <h3>TIM4 CH1–4 + TIM1 CH1 → 5 × PWM → MG996R</h3>
          <p>
            PB6 / PB7 / PB8 / PB9 + PA8 ·{" "}
            {t(
              bi(
                "head and arms mapping pending",
                "asignación de cabeza y brazos pendiente",
              ),
            )}
          </p>
          <p>
            {t(
              bi(
                "Carrier design evidence, not verified wiring. Hardware-generated pulses; proposed 20 ms control updates are separate from PWM generation. Dedicated servo supply and verified ground references required.",
                "Evidencia del diseño carrier, no cableado verificado. Pulsos generados por hardware; las actualizaciones de control propuestas de 20 ms son independientes del PWM. Se requiere fuente dedicada para servos y referencias de tierra verificadas.",
              ),
            )}
          </p>
        </article>
      </div>
      <div className="motion-demo">
        <h3>{t(bi("Follow a PAN goal", "Sigue un objetivo PAN"))}</h3>
        <p>
          {t(
            bi(
              "Simulated scenario: controller already armed with a fresh heartbeat. Each stage is slowed for explanation; values and timing are illustrative.",
              "Escenario simulado: controlador ya armado con heartbeat reciente. Cada etapa se ralentiza para explicarla; valores y tiempos son ilustrativos.",
            ),
          )}
        </p>
        <div className="motion-controls">
          {!reduced && (
            <button
              type="button"
              onClick={() => {
                if (!playing && step >= 7) setStep(-1);
                setPlaying(!playing);
              }}
            >
              {t(
                playing
                  ? bi("Pause simulation", "Pausar simulación")
                  : bi("Play simulation", "Reproducir simulación"),
              )}
            </button>
          )}
          <button
            type="button"
            disabled={step >= 7}
            onClick={() => {
              setPlaying(false);
              setStep(step + 1);
            }}
          >
            {t(bi("Next step", "Siguiente paso"))}
          </button>
          <button
            type="button"
            onClick={() => {
              setPlaying(false);
              setStep(7);
            }}
          >
            {t(bi("Simulate heartbeat loss", "Simular pérdida de heartbeat"))}
          </button>
          <button
            type="button"
            onClick={() => {
              setPlaying(false);
              setStep(-1);
            }}
          >
            {t(bi("Reset demo", "Reiniciar demo"))}
          </button>
        </div>
        <p className="motion-demo-status" role="status">
          {step < 0
            ? t(
                bi(
                  "Simulated · ready to explore. No data is transmitted.",
                  "Simulated · listo para explorar. No se transmiten datos.",
                ),
              )
            : `${step + 1}/8 · ${t(motionSteps[step])}`}
        </p>
        <ol>
          {motionSteps.map((copy, i) => (
            <li key={i} aria-current={step === i ? "step" : undefined}>
              {t(copy)}
            </li>
          ))}
        </ol>
      </div>
      <details className="motion-why">
        <summary>
          {t(
            bi(
              "Why FreeRTOS alongside Linux?",
              "¿Por qué FreeRTOS junto a Linux?",
            ),
          )}
        </summary>
        <p>
          {t(
            bi(
              "Linux keeps vision, voice and planning flexible. A dedicated microcontroller can isolate periodic control and safety supervision from those workloads. FreeRTOS schedules the tasks; timer peripherals generate PWM independently. Determinism still requires measured execution times, interrupt budgets and hardware validation.",
              "Linux mantiene flexibles la visión, la voz y la planificación. Un microcontrolador dedicado puede aislar el control periódico y la supervisión de seguridad de esas cargas. FreeRTOS organiza las tareas; los periféricos timer generan PWM de forma independiente. El determinismo aún exige medir tiempos de ejecución, presupuestos de interrupciones y validar el hardware.",
            ),
          )}
        </p>
        <a
          className="text-link"
          href={source("docs/freertos-motion-control.md")}
          target="_blank"
          rel="noreferrer"
        >
          {t(
            bi(
              "Architecture, testing & hardware checklist ↗",
              "Arquitectura, pruebas y verificaciones pendientes ↗",
            ),
          )}
        </a>
      </details>
    </section>
  );
}
function Flow({ label, active }: { label: string; active: boolean }) {
  return (
    <div className="motion-flow" data-active={active}>
      <svg width="30" height="44" viewBox="0 0 30 44" aria-hidden="true">
        <path
          d="M10 2v36m-6-6 6 6 6-6M23 40V4m-5 6 5-6 5 6"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        />
      </svg>
      <span>{label}</span>
    </div>
  );
}

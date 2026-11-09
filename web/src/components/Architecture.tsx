import { useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  Camera,
  CircuitBoard,
  Cpu,
  Mic,
  Monitor,
  Radio,
} from "lucide-react";
import {
  bi,
  components,
  source,
  stageNames,
  type ComponentId,
} from "../data/project";
import { useLocale } from "../state/Locale";
const nodes = [
  { id: "camera", icon: Camera, label: "OV5647", bus: "CSI" },
  { id: "audio", icon: Mic, label: "ReSpeaker", bus: "I²C + I²S" },
  { id: "display", icon: Monitor, label: "Display-G", bus: "SPI" },
] as const;
export default function Architecture() {
  const { t } = useLocale();
  const [selected, setSelected] = useState<ComponentId>("pi");
  const component = components.find((c) => c.id === selected)!;
  return (
    <div className="architecture-layout">
      <div className="architecture-board">
        <div className="diagram-label">
          <Radio size={13} />
          {t(
            bi(
              "ROBOT ARCHITECTURE · NOT LIVE TELEMETRY",
              "ARQUITECTURA DEL ROBOT · SIN TELEMETRÍA EN VIVO",
            ),
          )}
        </div>
        <div className="peripherals">
          {nodes.map((n) => (
            <div className="peripheral" key={n.id}>
              <button
                onClick={() => setSelected(n.id)}
                aria-pressed={selected === n.id}
              >
                <n.icon size={22} />
                <strong>{n.label}</strong>
              </button>
              <span className="bus">
                <i />
                {n.bus}
                <ArrowDown size={13} />
              </span>
            </div>
          ))}
        </div>
        <button
          className="pi-node"
          onClick={() => setSelected("pi")}
          aria-pressed={selected === "pi"}
        >
          <Cpu size={29} />
          <div>
            <small>
              {t(bi("HIGH-LEVEL COMPUTE", "CÓMPUTO DE ALTO NIVEL"))}
            </small>
            <strong>Raspberry Pi 5</strong>
            <span>
              {t(
                bi(
                  "AI providers · Audio · Computer vision",
                  "Proveedores IA · Audio · Visión",
                ),
              )}
              <br />
              {t(
                bi(
                  "Face rendering · High-level behavior",
                  "Renderizado de cara · Comportamiento",
                ),
              )}
            </span>
          </div>
          <span className="node-dot" />
        </button>
        <div className="future-bus">
          <span />
          <span>UART · {t(bi("planned", "planeado"))}</span>
          <ArrowDown size={17} />
        </div>
        <button
          className="stm-node"
          onClick={() => setSelected("stm")}
          aria-pressed={selected === "stm"}
        >
          <CircuitBoard size={28} />
          <div>
            <small>
              {t(
                bi("FUTURE REAL-TIME CONTROL", "FUTURO CONTROL EN TIEMPO REAL"),
              )}
            </small>
            <strong>STM32F401</strong>
            <span>
              {t(
                bi(
                  "PWM · Servo limits · Motor safety",
                  "PWM · Límites · Seguridad de motores",
                ),
              )}
            </span>
          </div>
        </button>
        <button
          className="servo-node"
          onClick={() => setSelected("servo")}
          aria-pressed={selected === "servo"}
        >
          <span className="dashed-line" />
          {t(bi("MG996R actuators", "Actuadores MG996R"))}
          <ArrowRight size={16} />
        </button>
        <div className="diagram-legend">
          <span>
            <i />
            {t(bi("Implemented interface", "Interfaz implementada"))}
          </span>
          <span>
            <i className="dashed" />
            {t(bi("Planned interface", "Interfaz planeada"))}
          </span>
        </div>
      </div>
      <aside className="architecture-detail" aria-live="polite">
        <span className="eyebrow">
          {t(bi("SELECT A BLOCK TO EXPLORE", "SELECCIONA UN BLOQUE"))}
        </span>
        <span className={`badge ${component.stage}`}>
          {t(stageNames[component.stage])}
        </span>
        <h3>{component.name}</h3>
        <p>{t(component.detail)}</p>
        <code>{component.interface}</code>
        <a
          className="text-link"
          href={source(component.path)}
          target="_blank"
          rel="noreferrer"
        >
          {t(bi("Inspect the source", "Revisar el código"))}
          <ArrowRight size={16} />
        </a>
        <div className="architecture-note">
          {t(
            bi(
              "The carrier routes these interfaces; it does not replace firmware. The documented JLCPCB order includes 37 THT parts; fuse holders, fuses and the JP1 shunt are hand-fitted. Electrical checks follow receipt and assembly.",
              "La carrier distribuye estas interfaces; no reemplaza el firmware. El pedido documentado a JLCPCB incluye 37 piezas THT; los portafusibles, fusibles y el puente JP1 se montan a mano. Las pruebas eléctricas siguen a la recepción y al montaje.",
            ),
          )}
        </div>
      </aside>
    </div>
  );
}

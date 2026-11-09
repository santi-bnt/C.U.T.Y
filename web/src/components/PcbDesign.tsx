import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { Download, Move, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import EngineeringViewport from "./EngineeringViewport";
import {
  carrier,
  engineeringAsset,
  netKind,
  pcbPath,
  type BoardPart,
} from "../data/engineering";
import { boardFunction } from "../data/boardFunctions";
import { bi, source } from "../data/project";
import { useLocale } from "../state/Locale";
import { useMedia } from "../state/useMedia";

export default function PcbDesign() {
  const { t } = useLocale();
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [side, setSide] = useState<"front" | "back">("front");
  const [mode, setMode] = useState<"layout" | "3d">("layout");
  const [view3D, setView3D] = useState<"front" | "back" | "iso">("iso");
  const [reset3D, setReset3D] = useState(0);
  const [selected, setSelected] = useState("J12"),
    [hover, setHover] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1),
    [pan, setPan] = useState(false);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; y: number; box: number[] } | null>(null);
  const part = carrier.components.find((p) => p.ref === (hover ?? selected))!;
  useEffect(() => {
    const element = svg.current;
    if (!element) return;
    const focused = carrier.components.find((p) => p.ref === selected)!;
    const [x, y, w, h] = focused.bounds;
    const width = 100 / zoom,
      height = 92 / zoom;
    const center = side === "back" ? 100 - x - w / 2 : x + w / 2;
    const left = Math.max(0, Math.min(100 - width, center - width / 2));
    const top = Math.max(0, Math.min(92 - height, y + h / 2 - height / 2));
    const tween = gsap.to(element, {
      attr: { viewBox: `${left} ${top} ${width} ${height}` },
      duration: reduced ? 0 : 0.5,
      ease: "power2.inOut",
      overwrite: true,
    });
    return () => {
      tween.kill();
    };
  }, [selected, side, zoom, reduced, mode]);
  const focusPart = (ref: string) => {
    setSelected(ref);
    setHover(null);
    setZoom(1.8);
  };
  const bounds = (p: BoardPart) => {
    const [x, y, w, h] = p.bounds;
    return { x: side === "back" ? 100 - x - w : x, y, width: w, height: h };
  };
  return (
    <section
      id="pcb-design"
      data-scene="pcb"
      className="technical-section paper"
    >
      <div className="technical-heading">
        <span className="eyebrow">
          04 / {t(bi("PCB DESIGN", "DISEÑO PCB"))}
        </span>
        <h2 className="reveal-line">
          <span>{t(bi("Inside the circuit.", "Dentro del circuito."))}</span>
        </h2>
        <p>
          {t(
            bi(
              "A real carrier. Every pad accounted for. Explore the native layout behind C.U.T.Y.’s electronics.",
              "Una carrier real. Cada pad identificado. Explora el diseño nativo de la electrónica de C.U.T.Y.",
            ),
          )}
        </p>
      </div>
      <div className="engineering-notice">
        <strong>
          {t(
            bi(
              "JLCPCB THT ORDER / HAND-FIT PARTS + ELECTRICAL CHECKS PENDING",
              "PEDIDO THT EN JLCPCB / FALTAN PIEZAS A MANO Y PRUEBAS ELÉCTRICAS",
            ),
          )}
        </strong>
        <span>
          {t(
            bi(
              "Carrier V1.1 · 100 × 92 mm · 2 layers · 1.6 mm. JLCPCB soldered 37 THT parts; F1/F2 fuse holders and fuses, plus the JP1 shunt, are hand-fitted. Receipt and electrical validation remain pending.",
              "Carrier V1.1 · 100 × 92 mm · 2 capas · 1.6 mm. JLCPCB soldó 37 piezas THT; faltan a mano los portafusibles y fusibles F1/F2, además del puente JP1. Falta recibirla y validarla eléctricamente.",
            ),
          )}
        </span>
      </div>
      <div className="pcb-layout">
        <div className="pcb-inspector">
          <div className="engineering-toolbar">
            <div className="segmented">
              <button
                aria-pressed={mode === "layout"}
                onClick={() => setMode("layout")}
              >
                {t(bi("Actual layout", "Diseño real"))}
              </button>
              <button
                aria-pressed={mode === "3d"}
                onClick={() => setMode("3d")}
              >
                {t(bi("3D mechanical reference", "Referencia mecánica 3D"))}
              </button>
            </div>
            <span className="mono">43 {t(bi("footprints", "footprints"))}</span>
          </div>
          {mode === "3d" ? (
            <div className="pcb-reference-3d">
              <EngineeringViewport
                mode="pcb"
                selected={selected}
                hover={hover}
                onSelect={focusPart}
                onHover={setHover}
                view={view3D}
                zoom={zoom - 1}
                reset={reset3D}
              />
              <div className="assembly-controls">
                {(["front", "back", "iso"] as const).map((view, index) => (
                  <button
                    key={view}
                    aria-pressed={view3D === view}
                    onClick={() => setView3D(view)}
                  >
                    {t(
                      [
                        bi("Front 3D", "Frente 3D"),
                        bi("Back 3D", "Reverso 3D"),
                        bi("Isometric 3D", "Isométrica 3D"),
                      ][index],
                    )}
                  </button>
                ))}
                <button
                  onClick={() => setZoom((z) => Math.min(5, z + 0.5))}
                  aria-label={t(bi("Zoom PCB 3D in", "Acercar PCB 3D"))}
                >
                  <ZoomIn size={16} />
                </button>
                <button
                  onClick={() => setZoom((z) => Math.max(-2, z - 0.5))}
                  aria-label={t(bi("Zoom PCB 3D out", "Alejar PCB 3D"))}
                >
                  <ZoomOut size={16} />
                </button>
                <button
                  onClick={() => {
                    setZoom(1);
                    setView3D("iso");
                    setReset3D((r) => r + 1);
                  }}
                  aria-label={t(bi("Reset PCB 3D", "Restablecer PCB 3D"))}
                >
                  <RotateCcw size={16} />
                </button>
              </div>
              <p className="simulation-note">
                {t(
                  bi(
                    "This mechanical view comes from the November 5 Nido model. The printable enclosure was revised on November 6; its current renders and print files are linked below. Components are simplified envelopes. Native KiCad remains the electrical source; fuse positions differ between these references. Mounting holes and NT1 have no selectable 3D part.",
                    "Esta vista mecánica viene del modelo Nido del 5 de noviembre. La carcasa imprimible se revisó el 6 de noviembre; abajo están sus renders y archivos actuales. Los componentes son envolventes simplificadas. KiCad sigue como fuente eléctrica; las posiciones de fusibles difieren entre referencias. Los agujeros y NT1 no tienen pieza 3D seleccionable.",
                  ),
                )}
              </p>
            </div>
          ) : (
            <>
              <svg
                className={`pcb-canvas ${pan ? "pan-enabled" : ""}`}
                ref={svg}
                viewBox="0 0 100 92"
                tabIndex={0}
                role="group"
                aria-label={t(
                  bi(
                    "Actual carrier PCB layout. Select a footprint; use plus, minus or Home to zoom.",
                    "PCB real. Selecciona un footprint; usa más, menos o Inicio para zoom.",
                  ),
                )}
                onKeyDown={(event) => {
                  if (event.key === "+" || event.key === "=") {
                    event.preventDefault();
                    setZoom((z) => Math.min(3, z + 0.5));
                  }
                  if (event.key === "-") {
                    event.preventDefault();
                    setZoom((z) => Math.max(1, z - 0.5));
                  }
                  if (event.key === "Home") {
                    event.preventDefault();
                    setZoom(1);
                  }
                }}
                onPointerDown={(event) => {
                  if (!pan || (event.target as Element).closest("[data-ref]"))
                    return;
                  const box = event.currentTarget.viewBox.baseVal;
                  drag.current = {
                    x: event.clientX,
                    y: event.clientY,
                    box: [box.x, box.y, box.width, box.height],
                  };
                  event.currentTarget.setPointerCapture(event.pointerId);
                }}
                onPointerMove={(event) => {
                  if (!drag.current) return;
                  const [x, y, w, h] = drag.current.box,
                    rect = event.currentTarget.getBoundingClientRect();
                  const nx = Math.max(
                    0,
                    Math.min(
                      100 - w,
                      x - ((event.clientX - drag.current.x) / rect.width) * w,
                    ),
                  );
                  const ny = Math.max(
                    0,
                    Math.min(
                      92 - h,
                      y - ((event.clientY - drag.current.y) / rect.height) * h,
                    ),
                  );
                  event.currentTarget.setAttribute(
                    "viewBox",
                    `${nx} ${ny} ${w} ${h}`,
                  );
                }}
                onPointerUp={() => {
                  drag.current = null;
                }}
                onPointerCancel={() => {
                  drag.current = null;
                }}
              >
                <image
                  href={engineeringAsset(`carrier-${side}.png`)}
                  width="100"
                  height="92"
                  preserveAspectRatio="none"
                />
                {carrier.components.map((p) => (
                  <g
                    key={p.ref}
                    role="button"
                    tabIndex={0}
                    data-ref={p.ref}
                    className={`pcb-hotspot ${selected === p.ref ? "selected" : ""} ${hover === p.ref ? "hovered" : ""}`}
                    aria-label={`${t(bi("Select PCB component", "Seleccionar componente PCB"))} ${p.ref}`}
                    aria-pressed={selected === p.ref}
                    onPointerEnter={() => setHover(p.ref)}
                    onPointerLeave={() => setHover(null)}
                    onFocus={() => setHover(p.ref)}
                    onBlur={() => setHover(null)}
                    onClick={() => {
                      focusPart(p.ref);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        focusPart(p.ref);
                      }
                    }}
                  >
                    <title>
                      {p.ref} / {p.value}
                    </title>
                    <rect {...bounds(p)} rx=".5" />
                  </g>
                ))}
              </svg>
              <div className="engineering-toolbar">
                <div className="segmented">
                  <button
                    aria-pressed={side === "front"}
                    onClick={() => setSide("front")}
                  >
                    {t(bi("Front", "Frente"))}
                  </button>
                  <button
                    aria-pressed={side === "back"}
                    onClick={() => setSide("back")}
                  >
                    {t(bi("Back", "Reverso"))}
                  </button>
                </div>
                <div className="pcb-actions">
                  <button
                    className="icon-button"
                    aria-label={t(bi("Zoom PCB in", "Acercar PCB"))}
                    disabled={zoom === 3}
                    onClick={() => setZoom((z) => Math.min(3, z + 0.5))}
                  >
                    <ZoomIn size={18} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label={t(bi("Zoom PCB out", "Alejar PCB"))}
                    disabled={zoom === 1}
                    onClick={() => setZoom((z) => Math.max(1, z - 0.5))}
                  >
                    <ZoomOut size={18} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label={t(bi("Pan PCB", "Desplazar PCB"))}
                    aria-pressed={pan}
                    onClick={() => setPan((v) => !v)}
                  >
                    <Move size={18} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label={t(bi("Reset PCB view", "Restablecer PCB"))}
                    onClick={() => {
                      setZoom(1);
                      setPan(false);
                      setSide("front");
                    }}
                  >
                    <RotateCcw size={18} />
                  </button>
                </div>
              </div>
            </>
          )}
          <p className="caption">
            {t(
              bi(
                "Actual Gerber previews; selectable bounds come from native KiCad pad coordinates. Back view is mirrored. This is a 2D layout, not an assembled 3D board.",
                "Gerbers reales; las áreas seleccionables vienen de coordenadas de pads KiCad. Reverso reflejado. Es un diseño 2D, no una PCB 3D ensamblada.",
              ),
            )}
          </p>
        </div>
        <aside className="pcb-details" aria-live="polite">
          <span className="eyebrow">
            {t(bi("FOOTPRINT INSPECTOR", "INSPECTOR DE FOOTPRINTS"))}
          </span>
          <div className="pcb-component-title">
            <strong>{part.ref}</strong>
            <h3>{part.value}</h3>
          </div>
          <p>{t(boardFunction(part))}</p>
          <dl>
            <div>
              <dt>{t(bi("Function group", "Grupo funcional"))}</dt>
              <dd>{part.group}</dd>
            </div>
            <div>
              <dt>{t(bi("BOM part", "Componente BOM"))}</dt>
              <dd>{part.mpn || t(bi("Not specified", "No especificado"))}</dd>
            </div>
          </dl>
          <a
            className="text-link"
            href={source(pcbPath)}
            target="_blank"
            rel="noreferrer"
          >
            {t(
              bi("Trace to native KiCad source ↗", "Ver fuente KiCad nativa ↗"),
            )}
          </a>
          <div className="pcb-part-picker">
            <label htmlFor="pcb-part">
              {t(bi("Select component", "Seleccionar componente"))}
            </label>
            <select
              id="pcb-part"
              value={selected}
              onChange={(event) => {
                focusPart(event.target.value);
              }}
            >
              {carrier.components.map((p) => (
                <option value={p.ref} key={p.ref}>
                  {p.ref} / {p.value}
                </option>
              ))}
            </select>
          </div>
          <div className="pin-scroll">
            <table>
              <thead>
                <tr>
                  <th>{t(bi("Pin", "Pin"))}</th>
                  <th>{t(bi("Assigned net", "Red asignada"))}</th>
                </tr>
              </thead>
              <tbody>
                {part.pins.map((pin) => (
                  <tr key={pin.pin}>
                    <td>
                      {pin.pin}
                      {pin.label ? ` / ${pin.label}` : ""}
                    </td>
                    <td>
                      <i className={`net-dot ${netKind(pin.net)}`} />
                      {pin.net || t(bi("Not connected", "Sin conectar"))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </aside>
      </div>
      <div className="engineering-downloads">
        {[
          [
            "carrier-project.zip",
            bi("KiCad project + libraries", "Proyecto KiCad + bibliotecas"),
          ],
          ["carrier.kicad_pcb", bi("PCB layout", "Diseño PCB")],
          ["carrier.kicad_sch", bi("Schematic source", "Fuente del esquema")],
          ["carrier-schematic.pdf", bi("Schematic PDF", "Esquema PDF")],
          ["carrier-bom.csv", bi("Bill of materials", "Lista de materiales")],
          ["carrier-gerbers.zip", bi("Gerbers + drills", "Gerbers + taladros")],
          ["project-bom.md", bi("Project hardware BOM", "BOM general del proyecto")],
          ["carrier-readme.md", bi("Carrier documentation", "Documentación carrier")],
        ].map(([file, label]) => (
          <a
            key={file as string}
            href={engineeringAsset(file as string)}
            download
          >
            <Download size={15} />
            {t(label as { en: string; es: string })}
          </a>
        ))}
      </div>
      <details className="pcb-order-files">
        <summary>
          {t(bi("Assembly order files & alternatives", "Archivos del pedido y alternativa PCBA"))}
        </summary>
        <p>
          {t(
            bi(
              "The README records JLCPCB as the ordered supplier. PCBWay files are retained as an alternative package, not as the order that was placed.",
              "El README registra a JLCPCB como proveedor del pedido. Los archivos de PCBWay se conservan como alternativa, no como el pedido realizado.",
            ),
          )}
        </p>
        <div className="engineering-downloads">
          {[
            ["jlcpcb-bom.csv", bi("JLCPCB BOM", "BOM de JLCPCB")],
            ["jlcpcb-cpl.csv", bi("JLCPCB placement (CPL)", "Posiciones JLCPCB (CPL)")],
            ["jlcpcb-order-notes.md", bi("JLCPCB order notes", "Notas del pedido JLCPCB")],
            ["pcba-assembly.pdf", bi("PCBWay assembly drawing", "Plano de ensamble PCBWay")],
            ["pcba-bom.xlsx", bi("PCBWay PCBA BOM", "BOM PCBA PCBWay")],
            ["pcba-cpl.xlsx", bi("PCBWay PCBA placement", "Posiciones PCBA PCBWay")],
            ["pcba-readme.md", bi("PCBWay alternative instructions", "Instrucciones alternativa PCBWay")],
          ].map(([file, label]) => (
            <a
              key={file as string}
              href={engineeringAsset(file as string)}
              download
            >
              <Download size={15} />
              {t(label as { en: string; es: string })}
            </a>
          ))}
        </div>
      </details>
    </section>
  );
}

import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Download, Pause, Play } from "lucide-react";
import { bi } from "../data/project";
import { useLocale } from "../state/Locale";
const steps = [
  [
    "c_intro",
    "The complete companion",
    "El compañero completo",
    "From individual parts to a physical personality.",
    "De piezas individuales a una personalidad física.",
  ],
  [
    "imprime",
    "Made in layers",
    "Hecho por capas",
    "27 printable parts in the fixed-base CAD package.",
    "27 piezas imprimibles en el paquete CAD de base fija.",
  ],
  [
    "c_piso",
    "Start from the ground",
    "Desde la base",
    "The pedestal floor supports the fixed base.",
    "El piso del pedestal sostiene la base fija.",
  ],
  [
    "c_poste",
    "A fixed reference",
    "Un punto fijo",
    "The pedestal forms the stationary base.",
    "El pedestal forma la base inmóvil.",
  ],
  [
    "c_varillas",
    "A removable drawer",
    "Un cajón extraíble",
    "The battery drawer slides into the pedestal.",
    "El cajón de batería se desliza dentro del pedestal.",
  ],
  [
    "c_cubierta",
    "Support for the core",
    "Soporte para el núcleo",
    "The riser sits on the fixed pedestal.",
    "El soporte se coloca sobre el pedestal fijo.",
  ],
  [
    "c_cruceta",
    "The core deck",
    "La plataforma del núcleo",
    "The fixed deck mounts on the riser.",
    "La plataforma fija se monta sobre el soporte.",
  ],
  [
    "c_plataforma",
    "A place for everything",
    "Un lugar para todo",
    "The spine rises from the fixed deck.",
    "La columna se levanta desde la plataforma fija.",
  ],
  [
    "c_placa",
    "The circuit within",
    "El circuito interior",
    "The carrier and audio board sit on the spine.",
    "La carrier y el audio se ubican en la columna.",
  ],
  [
    "c_pi",
    "A compact brain",
    "Un cerebro compacto",
    "Raspberry Pi 5 occupies the other side of the core.",
    "La Raspberry Pi 5 ocupa el otro lado del núcleo.",
  ],
  [
    "c_rack",
    "Power has its place",
    "La potencia tiene su lugar",
    "The revised rack accommodates the documented converter envelopes.",
    "El rack revisado aloja las envolventes documentadas de convertidores.",
  ],
  [
    "c_hombros",
    "Room to express",
    "Espacio para expresarse",
    "The shoulder structure houses the arm servos.",
    "La estructura de hombros aloja los servos de brazos.",
  ],
  [
    "c_visor",
    "A window to personality",
    "Una ventana a su personalidad",
    "The display and camera share the visor assembly.",
    "Pantalla y cámara comparten el conjunto del visor.",
  ],
  [
    "c_cabeza",
    "A familiar face",
    "Una cara familiar",
    "The head closes around the visor.",
    "La cabeza cierra alrededor del visor.",
  ],
  [
    "c_carcasa",
    "The outer character",
    "El carácter exterior",
    "Front and rear shells cover the mechanical core.",
    "Panza y espalda cubren el núcleo mecánico.",
  ],
  [
    "c_brazos",
    "Small gestures",
    "Pequeños gestos",
    "Both arms move around their shoulder joints in a visual simulation.",
    "Ambos brazos se mueven sobre sus articulaciones en una simulación visual.",
  ],
  [
    "c_bateria",
    "A removable home",
    "Un espacio extraíble",
    "The drawer and battery are shown pulled out from the rear of the pedestal.",
    "El cajón y la batería se muestran extraídos por la parte trasera del pedestal.",
  ],
  [
    "c_listo",
    "Taking shape",
    "Tomando forma",
    "A visual assembly reference, not evidence of completed fabrication.",
    "Una referencia visual de ensamble, no prueba de fabricación terminada.",
  ],
] as const;
const asset = (name: string) => `${import.meta.env.BASE_URL}assembly/${name}`;
const currentRevision = [
  ["front", "Front", "Frente", "latest-front.png"],
  ["back", "Back", "Espalda", "latest-back.png"],
  ["side", "Side", "Lateral", "latest-side.png"],
  ["xray", "X-ray", "Rayos X", "latest-xray.png"],
] as const;
export default function AssemblyStory() {
  const { locale, t } = useLocale();
  const [step, setStep] = useState(0),
    [playing, setPlaying] = useState(false);
  const [revisionView, setRevisionView] = useState<(typeof currentRevision)[number][0]>("front");
  const current = steps[step];
  const selectedRevision = currentRevision.find(([id]) => id === revisionView)!;
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(
      () => setStep((s) => (s + 1) % steps.length),
      2200,
    );
    return () => window.clearInterval(timer);
  }, [playing]);
  return (
    <section id="assembly" className="assembly-story technical-section paper">
      <div className="technical-heading">
        <span className="eyebrow">
          V17 / FIJO · 13 NOV 2026 — {t(bi("CURRENT PRINT CAD", "CAD DE IMPRESIÓN ACTUAL"))}
        </span>
        <h2>
          {t(
            bi(
              "A fit refined around real parts.",
              "Un ajuste afinado con piezas reales.",
            ),
          )}
        </h2>
        <p>
          {t(
            bi(
              "The fixed V17 version uses a stationary pedestal and three planned servos. Explore the author CAD views and 27 original printable STL files.",
              "El V17 fijo usa un pedestal inmóvil y tres servos previstos. Explora las vistas CAD y los 27 STL originales de impresión.",
            ),
          )}
        </p>
      </div>
      <div className="latest-cad">
        <figure className="latest-cad-image">
          <img
            src={asset(selectedRevision[3])}
            alt={t(bi(`V17 Fixed CAD view: ${selectedRevision[1]}`, `Vista CAD del V17 Fijo: ${selectedRevision[2]}`))}
            width="1100"
            height="1100"
            loading="lazy"
          />
          <figcaption className="mono">
            {t(bi("AUTHOR CAD RENDER · 13 NOV 2026", "RENDER CAD DEL AUTOR · 13 NOV 2026"))}
          </figcaption>
        </figure>
        <div className="latest-cad-copy">
          <span className="eyebrow">{t(bi("MEASURED FIT UPDATE", "AJUSTE CON MEDIDAS"))}</span>
          <h3>{t(bi("Camera cradle. Speaker pocket. A revised visor.", "Cuna para cámara. Espacio para bocina. Visor revisado."))}</h3>
          <p>
            {t(
              bi(
                "Fixed base, pedestal and torso; only head PAN and both arms have active servo joints. Physical fit and motion remain unvalidated.",
                "Base, pedestal y cuerpo fijos; solo la cabeza PAN y ambos brazos tienen servos activos. El ajuste y movimiento físicos siguen sin validar.",
              ),
            )}
          </p>
          <div className="latest-cad-views" aria-label={t(bi("CAD views", "Vistas CAD"))}>
            {currentRevision.map(([id, en, es]) => (
              <button
                key={id}
                aria-pressed={revisionView === id}
                onClick={() => setRevisionView(id)}
              >
                {t(bi(en, es))}
              </button>
            ))}
          </div>
          <p className="simulation-note">
            {t(
              bi(
                "The interactive GLB uses 27 original STL meshes with rigid placement. Purchased components are simplified; some fasteners and cable envelopes are omitted. Physical fit and motion remain unvalidated.",
                "El GLB interactivo usa 27 mallas STL originales colocadas rígidamente. Los componentes comprados son simplificados; faltan algunos tornillos y envolventes de cables. El ajuste y movimiento físicos siguen sin validar.",
              ),
            )}
          </p>
        </div>
      </div>
      <div className="assembly-stage">
        <div className="assembly-image">
          <picture>
            {(step === 15 || step === 16) && <source media="(prefers-reduced-motion: reduce)" srcSet={asset(`fixed-${step+1}-still.webp?v=motion-20261118`)} />}
            <img
            src={asset(`fixed-${String(step + 1).padStart(2, "0")}.webp${step === 15 || step === 16 ? "?v=motion-20261118" : ""}`)}
            alt={locale === "en" ? current[1] : current[2]}
            loading="lazy"
            width="1218"
            height="1080"
          />
          </picture>
          <span className="mono">
            {String(step + 1).padStart(2, "0")} / 18 —{" "}
            {t(bi("FIXED CAD · VISUAL SEQUENCE", "CAD FIJO · SECUENCIA VISUAL"))}
          </span>
        </div>
        <div className="assembly-caption">
          <span className="eyebrow">
            {t(bi("FROM PART TO COMPANION", "DE PIEZA A COMPAÑERO"))}
          </span>
          <h3>{locale === "en" ? current[1] : current[2]}</h3>
          <p>{locale === "en" ? current[3] : current[4]}</p>
          <div className="assembly-playback">
            <button
              aria-label={t(
                bi("Previous assembly step", "Paso anterior de ensamble"),
              )}
              onClick={() => setStep((s) => (s + 17) % 18)}
            >
              <ArrowLeft size={18} />
            </button>
            <button
              aria-pressed={playing}
              onClick={() => setPlaying((p) => !p)}
            >
              {playing ? <Pause size={16} /> : <Play size={16} />}{" "}
              {t(
                playing
                  ? bi("Pause sequence", "Pausar secuencia")
                  : bi("Play sequence", "Reproducir secuencia"),
              )}
            </button>
            <button
              aria-label={t(
                bi("Next assembly step", "Paso siguiente de ensamble"),
              )}
              onClick={() => setStep((s) => (s + 1) % 18)}
            >
              <ArrowRight size={18} />
            </button>
          </div>
          <p className="simulation-note">
            {t(
              bi(
              "This visual sequence uses the fixed-pedestal GLB and original STL meshes. Purchased components are simplified, and physical fit remains unverified.",
              "Esta secuencia visual usa el GLB de pedestal fijo y las mallas STL originales. Los componentes comprados son simplificados y el ajuste físico sigue sin verificar.",
              ),
            )}
          </p>
          <a className="text-link" href="#explorer">
            {t(
              bi(
                "Inspect the revised robot in 3D ↗",
                "Inspeccionar el robot revisado en 3D ↗",
              ),
            )}
          </a>
        </div>
      </div>
      <div
        className="assembly-strip"
        aria-label={t(bi("Assembly chapters", "Capítulos de ensamble"))}
      >
        {steps.map((s, i) => (
          <button
            key={s[0]}
            aria-pressed={step === i}
            onClick={() => {
              setStep(i);
              setPlaying(false);
            }}
          >
            <img
              loading="lazy"
              src={asset(`fixed-${String(i + 1).padStart(2, "0")}${i === 15 || i === 16 ? "-still.webp?v=motion-20261118" : ".webp"}`)}
              width="110"
              height="98"
              alt=""
            />
            <span>
              {String(i + 1).padStart(2, "0")} / {locale === "en" ? s[1] : s[2]}
            </span>
          </button>
        ))}
      </div>
      <details className="cad-evidence">
        <summary>
          {t(
            bi(
              "CAD sources & manufacturing files",
              "Fuentes CAD y archivos de fabricación",
            ),
          )}
        </summary>
        <p>
          {t(
            bi(
                "The fixed print package includes 27 original STL parts, source references, dimensions and the author's verification report. The report has not been independently rerun here; physical fit, wiring and motor safety still need their own checks.",
                "El paquete fijo incluye 27 STL originales, referencias CAD, dimensiones y el reporte del autor. El ajuste físico y la seguridad de motores siguen pendientes.",
            ),
          )}
        </p>
        <div className="engineering-downloads">
          {[
            ["fixed-print-stl.zip", "27 STL · 13 Nov"],
            ["fixed-source-readme.md", "README · 13 Nov"],
            ["fixed-cad-source.zip", "CAD source / Fuente CAD"],
            ["fixed-print-parts.json", "Dimensions / Medidas"],
            ["fixed-author-cad-verification.json", "CAD report / Reporte CAD"],
            ["provenance.json", "Provenance / Procedencia"],
          ].map(([file, label]) => (
            <a href={asset(file)} key={file} download>
              <Download size={15} />
              {label}
            </a>
          ))}
        </div>
      </details>
    </section>
  );
}

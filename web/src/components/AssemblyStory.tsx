import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Download, Pause, Play } from "lucide-react";
import { bi } from "../data/project";
import { useLocale } from "../state/Locale";
import { useMedia } from "../state/useMedia";
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
    "30 printable parts in the supplied revised CAD package.",
    "30 piezas imprimibles en el paquete CAD revisado.",
  ],
  [
    "c_piso",
    "Start from the ground",
    "Desde la base",
    "The floor carries the two gimbal servos.",
    "El piso aloja los dos servos del gimbal.",
  ],
  [
    "c_poste",
    "A fixed reference",
    "Un punto fijo",
    "The post supports the universal joint.",
    "El poste sostiene la junta universal.",
  ],
  [
    "c_varillas",
    "Translate the motion",
    "Transmitir movimiento",
    "Cranks and connecting rods link the base to the platform.",
    "Manivelas y varillas conectan la base con la plataforma.",
  ],
  [
    "c_cubierta",
    "The nest",
    "El nido",
    "The cover encloses the stationary base.",
    "La cubierta envuelve la base fija.",
  ],
  [
    "c_cruceta",
    "Two axes, one joint",
    "Dos ejes, una junta",
    "A mechanical view of the universal joint.",
    "Una vista mecánica de la junta universal.",
  ],
  [
    "c_plataforma",
    "A place for everything",
    "Un lugar para todo",
    "The deck provides the mounting structure.",
    "La plataforma ofrece la estructura de montaje.",
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
    "Separate arm parts now support visual motion demonstrations.",
    "Las piezas separadas permiten demostraciones visuales de movimiento.",
  ],
  [
    "c_bateria",
    "A removable home",
    "Un espacio extraíble",
    "The revised drawer follows the battery envelope in the supplied CAD.",
    "El cajón revisado sigue la envolvente de batería del CAD recibido.",
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
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [step, setStep] = useState(0),
    [playing, setPlaying] = useState(false);
  const [revisionView, setRevisionView] = useState<(typeof currentRevision)[number][0]>("front");
  const current = steps[step];
  const selectedRevision = currentRevision.find(([id]) => id === revisionView)!;
  useEffect(() => {
    if (!playing || reduced) return;
    const timer = window.setInterval(
      () => setStep((s) => (s + 1) % steps.length),
      5500,
    );
    return () => window.clearInterval(timer);
  }, [playing, reduced]);
  return (
    <section id="assembly" className="assembly-story technical-section ink">
      <div className="technical-heading">
        <span className="eyebrow">
          V17 / NIDO · 06 NOV 2026 — {t(bi("CURRENT PRINT CAD", "CAD DE IMPRESIÓN ACTUAL"))}
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
              "The latest printable V17 Nido revision incorporates measured electronics, camera and speaker dimensions. Browse the author-provided design views and download the current print files.",
              "La última revisión imprimible del Nido V17 incorpora medidas de la electrónica, la cámara y la bocina. Explora las vistas del diseño y descarga los archivos actuales de impresión.",
            ),
          )}
        </p>
      </div>
      <div className="latest-cad">
        <figure className="latest-cad-image">
          <img
            src={asset(selectedRevision[3])}
            alt={t(bi(`V17 Nido CAD view: ${selectedRevision[1]}`, `Vista CAD del Nido V17: ${selectedRevision[2]}`))}
            width="1100"
            height="1100"
            loading="lazy"
          />
          <figcaption className="mono">
            {t(bi("AUTHOR CAD RENDER · 06 NOV 2026", "RENDER CAD DEL AUTOR · 06 NOV 2026"))}
          </figcaption>
        </figure>
        <div className="latest-cad-copy">
          <span className="eyebrow">{t(bi("MEASURED FIT UPDATE", "AJUSTE CON MEDIDAS"))}</span>
          <h3>{t(bi("Camera cradle. Speaker pocket. A revised visor.", "Cuna para cámara. Espacio para bocina. Visor revisado."))}</h3>
          <p>
            {t(
              bi(
                "The November 6 print CAD adds a camera cradle and retaining bar, sizes the display bars to the measured 5.8 mm panel, and shapes the grille around the 35.4 × 25 × 5.5 mm speaker. The battery drawer is designed for the team's HM2202 pack envelope; its exact dimensions still need measurement.",
                "El CAD de impresión del 6 de noviembre añade una cuna y barra para la cámara, ajusta las barras a la pantalla medida de 5.8 mm y forma la rejilla alrededor de la bocina de 35.4 × 25 × 5.5 mm. El cajón está diseñado para la batería HM2202 del equipo; aún falta medir sus dimensiones exactas.",
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
                "The supplied CAD report lists 30 watertight printable parts, 0 reported static interferences and 34 checked poses. Those are author-reported model checks, not physical print, assembly or electrical validation. The interactive GLB is rebuilt from this November 6 CAD revision, including the camera cradle and measured display/camera bars.",
                "El reporte CAD suministrado enumera 30 piezas imprimibles herméticas, 0 interferencias estáticas reportadas y 34 posturas revisadas. Son comprobaciones del modelo reportadas por el autor, no validación física de impresión, ensamble o electricidad. El GLB interactivo se reconstruyó desde esta revisión CAD del 6 de noviembre e incluye la cuna de cámara y las barras medidas para pantalla y cámara.",
              ),
            )}
          </p>
        </div>
      </div>
      <div className="assembly-stage">
        <div className="assembly-image">
          <img
            src={asset(current[0] + ".webp")}
            alt={locale === "en" ? current[1] : current[2]}
            loading="lazy"
            width="1218"
            height="1080"
          />
          <span className="mono">
            {String(step + 1).padStart(2, "0")} / 18 —{" "}
            {t(bi("EARLIER ASSEMBLY REFERENCE", "REFERENCIA DE ENSAMBLE ANTERIOR"))}
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
              disabled={reduced}
              aria-pressed={playing && !reduced}
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
              "This 18-step image sequence depicts an earlier Nido assembly reference. The interactive GLB and current November 6 printable CAD share the updated enclosure geometry; purchased electronics remain simplified CAD envelopes.",
              "Esta secuencia de 18 pasos muestra una referencia anterior de armado Nido. El GLB interactivo y la CAD imprimible actual del 6 de noviembre comparten la geometría nueva de la carcasa; los componentes electrónicos comprados siguen como envolventes CAD simplificadas.",
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
              src={asset(s[0] + ".webp")}
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
                "The November 6 print package includes 30 oriented STL parts, the matching CadQuery source, part dimensions and the author's verification report. The report has not been independently rerun here; physical fit, wiring and motor safety still need their own checks.",
                "El paquete de impresión del 6 de noviembre incluye 30 STL orientados, la fuente CadQuery correspondiente, dimensiones y el reporte de verificación del autor. Aquí no se volvió a ejecutar de forma independiente; ajuste físico, cableado y seguridad de motores aún requieren sus propias comprobaciones.",
            ),
          )}
        </p>
        <div className="engineering-downloads">
          {[
            ["nido-print-stl.zip", "30 STL · 06 Nov"],
            ["source-readme.md", "README · 06 Nov"],
            ["current-cad-source.zip", "CadQuery source / Fuente CadQuery"],
            ["print-parts.json", "Dimensions / Medidas"],
            ["author-cad-verification.json", "CAD report / Reporte CAD"],
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

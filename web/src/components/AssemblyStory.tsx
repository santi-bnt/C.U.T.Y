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
export default function AssemblyStory() {
  const { locale, t } = useLocale();
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [step, setStep] = useState(0),
    [playing, setPlaying] = useState(false);
  const current = steps[step];
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
          V17 / NIDO — {t(bi("THE ASSEMBLY", "EL ENSAMBLE"))}
        </span>
        <h2>
          {t(
            bi(
              "Personality, piece by piece.",
              "Personalidad, pieza por pieza.",
            ),
          )}
        </h2>
        <p>
          {t(
            bi(
              "Explore the supplied assembly imagery, then inspect the revised geometry in 3D.",
              "Explora las imágenes de ensamble y después inspecciona la geometría revisada en 3D.",
            ),
          )}
        </p>
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
            {t(bi("RENDERED ASSEMBLY REFERENCE", "REFERENCIA RENDERIZADA"))}
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
                "Images depict the earlier Nido reference. The interactive 3D uses the supplied November 5 revision. Purchased components are simplified CAD envelopes.",
                "Las imágenes muestran la referencia Nido anterior. El 3D usa la revisión del 5 de noviembre. Los componentes comprados son envolventes CAD simplificadas.",
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
              "30 STL parts, a source README and an author-supplied CAD check report. Physical fit, wiring and motor safety require their own checks; the supplied collision report has not been rerun here.",
              "30 STL, el README original y un reporte CAD del autor. Ajuste físico, cableado y seguridad de motores requieren sus propias comprobaciones; aquí no se volvió a ejecutar la revisión de colisiones.",
            ),
          )}
        </p>
        <div className="engineering-downloads">
          {[
            ["nido-print-stl.zip", "30 STL"],
            ["source-readme.md", "README"],
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

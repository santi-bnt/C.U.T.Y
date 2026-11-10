import {
  lazy,
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  ArrowDown,
  ArrowUpRight,
  Github,
  Menu,
  X,
  ChevronRight,
  Radio,
  RotateCcw,
} from "lucide-react";
import {
  bi,
  capabilities,
  components,
  milestones,
  repo,
  source,
  stageNames,
  type Copy,
} from "./data/project";
import { useLocale } from "./state/Locale";
import { FaceSimulationProvider } from "./state/FaceSimulation";
import { createStoryMotion, type StoryMotion } from "./viewer/storyMotion";
import { chapterIds } from "./viewer/choreography";
import Choreography from "./components/Choreography";
import Architecture from "./components/Architecture";
import FaceDemo from "./simulations/FaceDemo";
import IntroSequence from "./components/IntroSequence";
import AssemblyStory from "./components/AssemblyStory";
import { modelInfo } from "./data/model";
import PcbDesign from "./components/PcbDesign";
import WiringConnections from "./components/WiringConnections";
const RobotViewer = lazy(() => import("./viewer/RobotViewer"));

function Heading({ first, second }: { first: Copy; second?: Copy }) {
  const { t } = useLocale();
  return (
    <h2>
      <span className="reveal-line">
        <span>{t(first)}</span>
      </span>
      {second && (
        <span className="reveal-line">
          <span className="heading-accent">{t(second)}</span>
        </span>
      )}
    </h2>
  );
}
function Chapter({
  id,
  number,
  label,
  tone,
  side,
  children,
}: {
  id: string;
  number: string;
  label: Copy;
  tone: "ink" | "paper" | "surface";
  side: "left" | "right";
  children: ReactNode;
}) {
  const { t } = useLocale();
  return (
    <section id={id} className={`chapter ${tone} copy-${side}`}>
      <div className="chapter-index">
        <span>
          {number} / {t(label)}
        </span>
        <span>C.U.T.Y. / V17</span>
      </div>
      <div className="chapter-copy">{children}</div>
    </section>
  );
}
function Header({ motion }: { motion: StoryMotion }) {
  const { locale, setLocale, t } = useLocale();
  const [menu, setMenu] = useState(false);
  const header = useRef<HTMLElement>(null);
  const nav = [
    { id: "home", label: bi("Home", "Inicio") },
    { id: "companion", label: bi("Meet C.U.T.Y.", "Conoce a C.U.T.Y.") },
    { id: "hardware-explorer", label: bi("Technology", "Tecnología") },
    { id: "pcb-design", label: bi("PCB Design", "Diseño PCB") },
    { id: "wiring", label: bi("Wiring & Connections", "Conexiones") },
    { id: "development", label: bi("Development", "Desarrollo") },
    { id: "live", label: bi("C.U.T.Y. Live", "C.U.T.Y. Live") },
  ];
  useEffect(
    () =>
      motion.subscribe(() => {
        const chapter = Math.round(motion.progress);
        if (header.current) {
          header.current.dataset.tone = [1, 3, 5, 7].includes(chapter)
            ? "ink"
            : "paper";
          header.current
            .querySelectorAll<HTMLAnchorElement>("nav a")
            .forEach((link) => {
              if (link.hash === `#${chapterIds[chapter]}`)
                link.setAttribute("aria-current", "location");
              else link.removeAttribute("aria-current");
            });
        }
      }),
    [motion],
  );
  return (
    <header className="site-header" ref={header} data-tone="paper">
      <a className="wordmark" href="#home" aria-label="C.U.T.Y home">
        <img
          className="brand-icon"
          src={`${import.meta.env.BASE_URL}favicon.svg`}
          alt=""
          aria-hidden="true"
        />
        C.U.T.Y.
      </a>
      <nav
        className={menu ? "nav open" : "nav"}
        aria-label={t(bi("Main navigation", "Navegación principal"))}
      >
        {nav.map((n) => (
          <a key={n.id} href={`#${n.id}`} onClick={() => setMenu(false)}>
            {t(n.label)}
          </a>
        ))}
      </nav>
      <div className="header-actions">
        <div className="language">
          {(["en", "es"] as const).map((l) => (
            <button
              key={l}
              lang={l}
              aria-label={l === "en" ? "English" : "Español"}
              aria-pressed={locale === l}
              onClick={() => setLocale(l)}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>
        <button
          className="menu-toggle"
          aria-label={t(bi("Toggle navigation", "Abrir navegación"))}
          aria-expanded={menu}
          onClick={() => setMenu((v) => !v)}
        >
          {menu ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
    </header>
  );
}
export default function App() {
  return (
    <FaceSimulationProvider>
      <Portfolio />
    </FaceSimulationProvider>
  );
}
function Portfolio() {
  const { t } = useLocale();
  const motion = useMemo(() => createStoryMotion(), []);
  const [componentIndex, setComponentIndex] = useState(0),
    [capabilityIndex, setCapabilityIndex] = useState(0);
  const [introRun, setIntroRun] = useState(0);
  const component = components[componentIndex],
    capability = capabilities[capabilityIndex];
  const dashboard = dashboardUrl(import.meta.env.VITE_CUTY_DASHBOARD_URL);
  return (
    <div className="homepage">
      <IntroSequence key={introRun} replay={introRun > 0} />
      <a className="skip-link" href="#main">
        {t(bi("Skip to content", "Ir al contenido"))}
      </a>
      <Header motion={motion} />
      <Choreography motion={motion} />
      <Suspense
        fallback={
          <div className="loading-model" role="status">
            {t(bi("Preparing C.U.T.Y.…", "Preparando C.U.T.Y.…"))}
          </div>
        }
      >
        <RobotViewer motion={motion} />
      </Suspense>
      <main id="main">
        <section className="product-hero paper" id="home">
          <span id="explorer" className="anchor-alias" />
          <div className="hero-overline">
            <span>
              {t(
                bi(
                  "A PHYSICAL DESKTOP COMPANION",
                  "UN COMPAÑERO FÍSICO DE ESCRITORIO",
                ),
              )}
            </span>
            <span>AI / VISION / EMBEDDED</span>
          </div>
          <h1 aria-label="C.U.T.Y.">
            {"C.U.T.Y.".split("").map((letter, i) => (
              <span className="hero-letter-mask" key={i}>
                <span className={`hero-letter ${i === 7 ? "accent" : ""}`}>
                  {letter}
                </span>
              </span>
            ))}
          </h1>
          <div className="hero-copy">
            <p className="mono">Companion Unit That Yaps</p>
            <h2>
              {t(bi("A little body.", "Un pequeño cuerpo."))}
              <br />
              <span>{t(bi("A curious mind.", "Una mente curiosa."))}</span>
            </h2>
            <p>
              {t(
                bi(
                  "Multimodal AI, computer vision and embedded engineering. Made physical.",
                  "IA multimodal, visión artificial e ingeniería embebida. Con presencia física.",
                ),
              )}
            </p>
            <a className="button primary" href="#companion">
              {t(bi("Meet your companion", "Conoce a tu compañero"))}
              <ArrowUpRight size={17} />
            </a>
            <button
              className="hero-replay"
              onClick={() => setIntroRun((run) => run + 1)}
            >
              <RotateCcw size={15} />
              {t(bi("Replay intro", "Repetir animación"))}
            </button>
          </div>
          <div className="hero-baseline">
            <a href="#companion">
              <ArrowDown size={15} />
              {t(
                bi(
                  "SCROLL TO MEET C.U.T.Y.",
                  "DESPLAZA PARA CONOCER A C.U.T.Y.",
                ),
              )}
            </a>
            <span>
              {t(
                bi(
                  "REAL V17 ASSEMBLY / IN DEVELOPMENT",
                  "ENSAMBLAJE V17 REAL / EN DESARROLLO",
                ),
              )}
            </span>
          </div>
        </section>
        <Chapter
          id="companion"
          number="01"
          label={bi("MEET C.U.T.Y.", "CONOCE A C.U.T.Y.")}
          tone="ink"
          side="right"
        >
          <Heading
            first={bi("A familiar face.", "Una cara familiar.")}
            second={bi("An unfamiliar idea.", "Una idea distinta.")}
          />
          <p className="chapter-lead">
            {t(
              bi(
                "What if an AI had a place at your desk? A voice to talk with. Eyes that look back. A little personality, written in code.",
                "¿Y si una IA tuviera un lugar en tu escritorio? Una voz para conversar. Ojos que te miran. Un poco de personalidad, escrita en código.",
              ),
            )}
          </p>
          <div className="companion-facts">
            <span>
              {t(
                bi(
                  "Voice conversation tested on Raspberry Pi",
                  "Conversación probada en Raspberry Pi",
                ),
              )}
            </span>
            <span>
              {t(
                bi(
                  "Local vision & expression software developed",
                  "Visión local y expresiones desarrolladas",
                ),
              )}
            </span>
            <span>
              {t(
                bi(
                  "Physical servo motion remains planned",
                  "Movimiento físico de servos aún planeado",
                ),
              )}
            </span>
          </div>
          <a className="text-link" href="#intelligence">
            {t(bi("Meet its expressions", "Conoce sus expresiones"))}
            <ArrowUpRight size={16} />
          </a>
        </Chapter>
        <Chapter
          id="intelligence"
          number="02"
          label={bi("EXPRESSIONS", "EXPRESIONES")}
          tone="paper"
          side="left"
        >
          <Heading
            first={bi("Personality.", "Personalidad.")}
            second={bi("Pixel by pixel.", "Píxel a píxel.")}
          />
          <p className="chapter-lead">
            {t(
              bi(
                "The same face as the physical robot. Change an expression and watch the actual LCD come to life.",
                "La misma cara del robot físico. Cambia una expresión y observa el LCD real cobrar vida.",
              ),
            )}
          </p>
          <FaceDemo />
          <p className="offline-label">
            <Radio size={13} />
            {t(
              bi(
                "ORIGINAL RENDERER / OFFLINE DEMO",
                "RENDERIZADOR ORIGINAL / DEMO LOCAL",
              ),
            )}
          </p>
        </Chapter>
        <Chapter
          id="hardware-explorer"
          number="03"
          label={bi("INSIDE THE ROBOT", "DENTRO DEL ROBOT")}
          tone="ink"
          side="right"
        >
          <Heading
            first={bi("Built on real", "Construido con")}
            second={bi("engineering.", "ingeniería real.")}
          />
          <p className="chapter-lead">
            {t(
              bi(
                "A physical character takes more than a model. Explore the hardware and the boundaries behind it.",
                "Un personaje físico necesita más que un modelo. Explora el hardware y sus responsabilidades.",
              ),
            )}
          </p>
          <div className="hardware-selector">
            {components.map((c, i) => (
              <button
                key={c.id}
                aria-pressed={i === componentIndex}
                onClick={() => setComponentIndex(i)}
              >
                <span>0{i + 1}</span>
                {c.name}
                <ChevronRight size={14} />
              </button>
            ))}
          </div>
          <article className="hardware-evidence" aria-live="polite">
            <span className={`badge ${component.stage}`}>
              {t(stageNames[component.stage])}
            </span>
            <h3>{component.name}</h3>
            <p>{t(component.detail)}</p>
            <a
              className="text-link"
              href={source(component.path)}
              target="_blank"
              rel="noreferrer"
            >
              {t(bi("Inspect the source", "Revisar la fuente"))}
              <ArrowUpRight size={15} />
            </a>
          </article>
        </Chapter>
        <section className="technical-disclosure ink">
          <details>
            <summary>
              {t(
                bi(
                  "Explore the system architecture & specifications",
                  "Explora la arquitectura y especificaciones",
                ),
              )}
              <span>+</span>
            </summary>
            <div id="architecture">
              <div className="technical-heading">
                <span className="eyebrow">03.1 / SYSTEM ARCHITECTURE</span>
                <Heading
                  first={bi("Different layers.", "Distintas capas.")}
                  second={bi("One character.", "Un personaje.")}
                />
                <p>
                  {t(
                    bi(
                      "The Pi handles perception and expression. The planned STM32 layer owns deterministic motion. Select a block for evidence.",
                      "La Pi gestiona percepción y expresión. La futura STM32 gestionará movimiento determinista. Selecciona un bloque para ver su evidencia.",
                    ),
                  )}
                </p>
              </div>
              <Architecture />
            </div>
            <div className="capability-audit">
              <div className="capability-tabs">
                {capabilities.map((c, i) => (
                  <button
                    key={c.id}
                    aria-pressed={capabilityIndex === i}
                    onClick={() => setCapabilityIndex(i)}
                  >
                    {t(c.label)}
                    <ArrowUpRight size={15} />
                  </button>
                ))}
              </div>
              <article aria-live="polite">
                <h3>{t(capability.title)}</h3>
                <p>{t(capability.detail)}</p>
                <p className="evidence">{t(capability.evidence)}</p>
                <a
                  className="text-link"
                  href={source(capability.path)}
                  target="_blank"
                  rel="noreferrer"
                >
                  {t(
                    bi("Explore implementation ↗", "Explorar implementación ↗"),
                  )}
                </a>
              </article>
            </div>
            <dl id="specifications" className="hardware-specs">
              {components.map((c) => (
                <div key={c.id}>
                  <dt>{c.name}</dt>
                  <dd>{c.spec}</dd>
                </div>
              ))}
              <div>
                <dt>
                  {t(
                    bi("V17 oriented dimensions", "Dimensiones V17 orientado"),
                  )}
                </dt>
                <dd>
                  {modelInfo.boundsMm.map((n) => n.toFixed(1)).join(" × ")} mm
                </dd>
              </div>
              <div>
                <dt>
                  {t(bi("Assembly geometry", "Geometría del ensamblaje"))}
                </dt>
                <dd>
                  {modelInfo.triangles.toLocaleString("en-US")}{" "}
                  {t(
                    bi(
                      "triangles · named parts · visual motion demos",
                      "triángulos · piezas con nombre · demos visuales",
                    ),
                  )}
                </dd>
              </div>
            </dl>
            <a className="text-link" href="#pcb-design">
              {t(
                bi("Inspect the carrier design ↗", "Inspeccionar la carrier ↗"),
              )}
            </a>
          </details>
        </section>
        <AssemblyStory />
        <PcbDesign />
        <WiringConnections />
        <Chapter
          id="development"
          number="06"
          label={bi("DEVELOPMENT", "DESARROLLO")}
          tone="surface"
          side="left"
        >
          <Heading
            first={bi("An open build.", "Un desarrollo abierto.")}
            second={bi("An honest journey.", "Un camino honesto.")}
          />
          <div className="development-timeline">
            {milestones.map((milestone, i) => (
              <article key={milestone.stage}>
                <div>
                  <span className="mono">0{i + 1}</span>
                  <span className={`badge ${milestone.stage}`}>
                    {t(stageNames[milestone.stage])}
                  </span>
                </div>
                <h3>{t(milestone.title)}</h3>
                <ul>
                  {milestone.items.map((item) => (
                    <li key={item.en}>{t(item)}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
          <a
            className="text-link"
            href={source("docs/roadmap.md")}
            target="_blank"
            rel="noreferrer"
          >
            {t(bi("Read the development roadmap", "Leer el roadmap"))}
            <ArrowUpRight size={15} />
          </a>
        </Chapter>
        <Chapter
          id="live"
          number="07"
          label={bi("C.U.T.Y. LIVE", "C.U.T.Y. LIVE")}
          tone="ink"
          side="right"
        >
          <Heading
            first={bi("A window into", "Una ventana a")}
            second={bi("its world.", "su mundo.")}
          />
          <p className="chapter-lead">
            {t(
              bi(
                "The product story lives here. Connected robot controls belong in their own protected space.",
                "La historia del producto vive aquí. Los controles conectados necesitan su propio espacio protegido.",
              ),
            )}
          </p>
          <div className="live-status" data-connection="offline">
            <span className="offline-label">
              <Radio size={14} />
              {t(
                bi(
                  "ROBOT CONNECTION / OFFLINE",
                  "CONEXIÓN AL ROBOT / DESCONECTADA",
                ),
              )}
            </span>
            <h3>
              {t(
                bi(
                  "The robot is not connected.",
                  "El robot no está conectado.",
                ),
              )}
            </h3>
            <p>
              {t(
                bi(
                  "This release makes no camera, microphone or hardware requests. No authenticated dashboard is implemented in this repository.",
                  "Esta versión no accede a cámara, micrófono ni hardware. El repositorio aún no implementa un dashboard autenticado.",
                ),
              )}
            </p>
            {dashboard ? (
              <a
                className="button primary"
                href={dashboard}
                target="_blank"
                rel="noreferrer"
              >
                {t(bi("Open robot dashboard", "Abrir dashboard del robot"))}
                <ArrowUpRight size={16} />
              </a>
            ) : (
              <button className="button secondary" disabled>
                {t(bi("Dashboard not configured", "Dashboard sin configurar"))}
              </button>
            )}
            <a className="text-link" href="#intelligence">
              {t(bi("Try the face demo", "Prueba la cara"))}
              <ArrowUpRight size={15} />
            </a>
          </div>
        </Chapter>
        <section className="project-outro paper" id="about">
          <p className="eyebrow">
            {t(bi("BUILT OUT OF CURIOSITY", "CREADO POR CURIOSIDAD"))}
          </p>
          <h2>
            {t(bi("A small robot.", "Un robot pequeño."))}
            <br />
            <span>
              {t(bi("A world of possibilities.", "Un mundo de posibilidades."))}
            </span>
          </h2>
          <p>
            {t(
              bi(
                "C.U.T.Y. explores the meeting point of multimodal AI, computer vision and embedded systems. The challenge is integration: reliable audio, expressive feedback, and a safe path from behavior to physical motion.",
                "C.U.T.Y. explora el encuentro entre IA multimodal, visión artificial y sistemas embebidos. El reto es integrar audio confiable, expresión y un camino seguro del comportamiento al movimiento físico.",
              ),
            )}
          </p>
          <div className="outro-links">
            <a
              className="button primary"
              href={repo}
              target="_blank"
              rel="noreferrer"
            >
              <Github size={17} />
              {t(bi("Follow the build", "Sigue el desarrollo"))}
            </a>
            <a className="text-link" href="#architecture">
              {t(bi("Technical Architecture", "Arquitectura técnica"))}
              <ArrowUpRight size={15} />
            </a>
          </div>
        </section>
      </main>
      <footer className="product-footer paper">
        <a className="wordmark" href="#home">
          C.U.T.Y.
        </a>
        <p>
          {t(
            bi(
              "Independent engineering. Open by design.",
              "Ingeniería independiente. Abierto por diseño.",
            ),
          )}
        </p>
        <a href="#home">{t(bi("Back to top ↑", "Volver arriba ↑"))}</a>
        <button
          className="footer-replay"
          onClick={() => setIntroRun((run) => run + 1)}
        >
          {t(bi("Replay intro", "Repetir animación"))}
        </button>
      </footer>
    </div>
  );
}
export function dashboardUrl(value: string | undefined) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password
      ? url.href
      : null;
  } catch {
    return null;
  }
}

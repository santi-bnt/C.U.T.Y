import { lazy, Suspense, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  Braces,
  Check,
  ChevronRight,
  CircuitBoard,
  Code2,
  Cpu,
  Eye,
  Github,
  Menu,
  ScanFace,
  Sparkles,
  X,
} from "lucide-react";
import {
  bi,
  capabilities,
  components,
  milestones,
  repo,
  source,
  stageNames,
} from "./data/project";
import { useLocale } from "./state/Locale";
import Architecture from "./components/Architecture";
import FaceDemo from "./simulations/FaceDemo";
const RobotViewer = lazy(() => import("./viewer/RobotViewer"));
const icons = {
  voice: AudioLines,
  vision: ScanFace,
  face: Sparkles,
  tools: Braces,
};

export default function App() {
  const { locale, setLocale, t } = useLocale();
  const [menu, setMenu] = useState(false);
  const [componentIndex, setComponentIndex] = useState(0);
  const [capabilityIndex, setCapabilityIndex] = useState(0);
  const component = components[componentIndex];
  const capability = capabilities[capabilityIndex];
  const nav = [
    { id: "explorer", title: bi("Explorer", "Explorador") },
    { id: "intelligence", title: bi("Intelligence", "Inteligencia") },
    { id: "architecture", title: bi("Architecture", "Arquitectura") },
    { id: "development", title: bi("Build log", "Desarrollo") },
  ];
  return (
    <>
      <a className="skip-link" href="#main">
        {t(bi("Skip to content", "Ir al contenido"))}
      </a>
      <header className="header">
        <a href="#" className="wordmark" aria-label="C.U.T.Y home">
          <span className="brand-icon">
            <i />
            <i />
          </span>
          C.U.T.Y
        </a>
        <nav
          className={menu ? "nav open" : "nav"}
          aria-label={t(bi("Main navigation", "Navegación principal"))}
        >
          {nav.map((n) => (
            <a key={n.id} href={`#${n.id}`} onClick={() => setMenu(false)}>
              {t(n.title)}
            </a>
          ))}
        </nav>
        <div className="header-actions">
          <div className="language" aria-label={t(bi("Language", "Idioma"))}>
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
          <a
            href={repo}
            target="_blank"
            rel="noreferrer"
            className="github-icon"
            aria-label="GitHub"
          >
            <Github size={19} />
          </a>
          <button
            className="mobile-toggle icon-button"
            aria-label={t(bi("Toggle navigation", "Abrir navegación"))}
            aria-expanded={menu}
            onClick={() => setMenu((v) => !v)}
          >
            {menu ? <X size={21} /> : <Menu size={21} />}
          </button>
        </div>
      </header>
      <main id="main">
        <section className="hero shell">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="tiny-cross">+</span>
              {t(
                bi(
                  "AN OPEN EXPERIMENT IN COMPANIONSHIP",
                  "UN EXPERIMENTO ABIERTO DE COMPAÑÍA",
                ),
              )}
            </div>
            <h1>
              C.U.T.Y<span className="title-period">.</span>
            </h1>
            <p className="hero-subtitle">Cute Utility That Yaps</p>
            <h2>
              {t(bi("A little body.", "Un pequeño cuerpo."))}
              <br />
              <span>{t(bi("A curious mind.", "Una mente curiosa."))}</span>
            </h2>
            <p className="hero-description">
              {t(
                bi(
                  "An expressive desktop companion robot integrating multimodal AI, computer vision and embedded systems. Built to listen, look, and bring a little personality to your desk.",
                  "Un compañero de escritorio expresivo que integra IA multimodal, visión artificial y sistemas embebidos. Creado para escuchar, mirar y darle personalidad a tu escritorio.",
                ),
              )}
            </p>
            <div className="hero-buttons">
              <a className="button primary" href="#explorer">
                {t(bi("Explore the Robot", "Explorar el robot"))}
                <ArrowUpRight size={17} />
              </a>
              <a className="button secondary" href="#architecture">
                {t(bi("Technical Architecture", "Arquitectura técnica"))}
                <ArrowRight size={17} />
              </a>
            </div>
            <a
              className="hero-source text-link"
              href={repo}
              target="_blank"
              rel="noreferrer"
            >
              <Github size={16} />
              {t(bi("View on GitHub", "Ver en GitHub"))}
              <ArrowUpRight size={14} />
            </a>
            <div className="hero-footnote">
              <span className="status-dot amber" />
              {t(bi("IN ACTIVE DEVELOPMENT", "EN DESARROLLO ACTIVO"))}
              <span>AI × ROBOTICS × EMBEDDED</span>
            </div>
          </div>
          <Suspense
            fallback={
              <div className="explorer placeholder" role="status">
                {t(bi("Loading explorer…", "Cargando explorador…"))}
              </div>
            }
          >
            <RobotViewer />
          </Suspense>
        </section>
        <div className="discipline-strip">
          <div className="shell">
            <span>
              <Cpu size={17} />
              {t(bi("Multimodal AI", "IA multimodal"))}
            </span>
            <span>
              <Eye size={17} />
              {t(bi("Computer vision", "Visión artificial"))}
            </span>
            <span>
              <CircuitBoard size={17} />
              {t(bi("Embedded systems", "Sistemas embebidos"))}
            </span>
            <span>
              <Code2 size={17} />
              {t(bi("Open engineering", "Ingeniería abierta"))}
            </span>
          </div>
        </div>
        <section className="section shell" id="hardware-explorer">
          <div className="section-heading">
            <div>
              <div className="eyebrow">
                01 / {t(bi("THE PHYSICAL LAYER", "LA CAPA FÍSICA"))}
              </div>
              <h2>
                {t(bi("Small form.", "Formato pequeño."))}
                <br />
                <span>{t(bi("Many disciplines.", "Muchas disciplinas."))}</span>
              </h2>
            </div>
            <p>
              {t(
                bi(
                  "One assembly. A stack of ideas. Explore the components behind the character.",
                  "Un ensamblaje. Muchas ideas. Explora los componentes detrás del personaje.",
                ),
              )}
            </p>
          </div>
          <div className="component-browser">
            <div
              className="component-list"
              aria-label={t(bi("Hardware components", "Componentes físicos"))}
            >
              {components.map((c, i) => (
                <button
                  key={c.id}
                  onClick={() => setComponentIndex(i)}
                  aria-pressed={i === componentIndex}
                >
                  <span className="component-num">0{i + 1}</span>
                  <span>{c.name}</span>
                  <ChevronRight size={16} />
                </button>
              ))}
            </div>
            <article className="component-detail" aria-live="polite">
              <div className="detail-top">
                <span className="eyebrow">{t(component.tag)}</span>
                <span className={`badge ${component.stage}`}>
                  {t(stageNames[component.stage])}
                </span>
              </div>
              <div className="component-glyph">
                <Cpu size={65} strokeWidth={0.8} />
                <span>0{componentIndex + 1}</span>
              </div>
              <h3>{component.name}</h3>
              <p>{t(component.detail)}</p>
              <div className="detail-bottom">
                <code>{component.interface}</code>
                <a
                  href={source(component.path)}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`${t(bi("Source for", "Fuente de"))} ${component.name}`}
                >
                  <ArrowUpRight size={20} />
                </a>
              </div>
            </article>
          </div>
          <p className="caption">
            {t(
              bi(
                "The V23 GLB contains nine named meshes with materials, but no rig or animation clips. Component information is shown externally; this viewer does not articulate parts. World-space bounds: X 182.70 × Y 333.75 × Z 131.67 mm. Y is up.",
                "El GLB V23 contiene nueve mallas con nombres y materiales, sin rig ni clips de animación. La información de componentes es externa; este visor no articula piezas. Límites globales: X 182.70 × Y 333.75 × Z 131.67 mm. Y es vertical.",
              ),
            )}
          </p>
        </section>
        <section className="intelligence section" id="intelligence">
          <div className="shell">
            <div className="section-heading">
              <div>
                <div className="eyebrow">
                  02 /{" "}
                  {t(bi("THE PERSONALITY STACK", "LA PERSONALIDAD EN CÓDIGO"))}
                </div>
                <h2>
                  {t(bi("More than", "Más que"))}
                  <br />
                  <span>
                    {t(bi("a talking machine.", "una máquina que habla."))}
                  </span>
                </h2>
              </div>
              <p>
                {t(
                  bi(
                    "Voice, perception and expression meet in Python. Each layer has a role. Each claim has a source.",
                    "Voz, percepción y expresión se encuentran en Python. Cada capa tiene una función. Cada afirmación tiene una fuente.",
                  ),
                )}
              </p>
            </div>
            <div className="capability-layout">
              <div className="capability-panel">
                <div
                  className="capability-tabs"
                  aria-label={t(bi("AI capabilities", "Capacidades de IA"))}
                >
                  {capabilities.map((c, i) => {
                    const Icon = icons[c.icon as keyof typeof icons];
                    return (
                      <button
                        key={c.id}
                        aria-pressed={i === capabilityIndex}
                        onClick={() => setCapabilityIndex(i)}
                      >
                        <Icon size={19} />
                        <span>{t(c.label)}</span>
                        <ArrowUpRight size={16} />
                      </button>
                    );
                  })}
                </div>
                <article className="capability-content" aria-live="polite">
                  <h3>{t(capability.title)}</h3>
                  <p>{t(capability.detail)}</p>
                  <div className="evidence">
                    <Check size={15} />
                    <span>{t(capability.evidence)}</span>
                  </div>
                  <a
                    className="text-link"
                    href={source(capability.path)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {t(bi("Explore implementation", "Explorar implementación"))}
                    <ArrowRight size={16} />
                  </a>
                </article>
              </div>
              <FaceDemo />
            </div>
          </div>
        </section>
        <section className="section shell" id="architecture">
          <div className="section-heading">
            <div>
              <div className="eyebrow">
                03 /{" "}
                {t(
                  bi(
                    "FROM PERCEPTION TO EXPRESSION",
                    "DE PERCEPCIÓN A EXPRESIÓN",
                  ),
                )}
              </div>
              <h2>
                {t(bi("One robot.", "Un robot."))}
                <br />
                <span>
                  {t(bi("Clear boundaries.", "Responsabilidades claras."))}
                </span>
              </h2>
            </div>
            <p>
              {t(
                bi(
                  "The Pi thinks and renders. The future STM32 layer will handle deterministic movement. Explore how the pieces connect.",
                  "La Pi piensa y renderiza. La futura capa STM32 gestionará el movimiento determinista. Explora cómo se conectan.",
                ),
              )}
            </p>
          </div>
          <Architecture />
        </section>
        <section className="section development" id="development">
          <div className="shell">
            <div className="section-heading">
              <div>
                <div className="eyebrow">
                  04 / {t(bi("ENGINEERING, IN THE OPEN", "INGENIERÍA ABIERTA"))}
                </div>
                <h2>
                  {t(bi("A work in progress.", "Un trabajo en progreso."))}
                  <br />
                  <span>
                    {t(
                      bi("With a clear direction.", "Con una dirección clara."),
                    )}
                  </span>
                </h2>
              </div>
              <div>
                <p>
                  {t(
                    bi(
                      "Software exists. Hardware earns its confidence through testing. These are different milestones.",
                      "El software existe. El hardware gana confianza mediante pruebas. Son hitos distintos.",
                    ),
                  )}
                </p>
                <a
                  className="text-link"
                  href={source("docs/roadmap.md")}
                  target="_blank"
                  rel="noreferrer"
                >
                  {t(bi("Read the roadmap", "Leer el roadmap"))}
                  <ArrowUpRight size={15} />
                </a>
              </div>
            </div>
            <div className="status-grid">
              {milestones.map((m, i) => (
                <article key={m.stage} className={`milestone ${m.stage}`}>
                  <div className="milestone-header">
                    <span className={`badge ${m.stage}`}>
                      {t(stageNames[m.stage])}
                    </span>
                    <span>0{i + 1}</span>
                  </div>
                  <h3>{t(m.title)}</h3>
                  <ul>
                    {m.items.map((item) => (
                      <li key={item.en}>
                        <span />
                        {t(item)}
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
            <p className="caption">
              {t(
                bi(
                  "Reviewed against the repository and documented physical checks · November 2026. No progress percentages or unmeasured performance claims.",
                  "Revisado contra el repositorio y las pruebas físicas documentadas · Noviembre 2026. Sin porcentajes de avance ni rendimiento sin medir.",
                ),
              )}
            </p>
          </div>
        </section>
        <section className="section shell specs" id="specifications">
          <div>
            <div className="eyebrow">
              05 / {t(bi("HARDWARE NOTES", "NOTAS DE HARDWARE"))}
            </div>
            <h2>{t(bi("Under the shell.", "Bajo la carcasa."))}</h2>
            <p>
              {t(
                bi(
                  "A modular hardware stack. A custom carrier to bring it together.",
                  "Hardware modular. Una carrier propia para unirlo.",
                ),
              )}
            </p>
            <a
              className="text-link"
              href={source("hardware/electronics/kicad/cuty_carrier")}
              target="_blank"
              rel="noreferrer"
            >
              {t(
                bi(
                  "KiCad files + fabrication exports",
                  "Archivos KiCad + fabricación",
                ),
              )}
              <ArrowUpRight size={16} />
            </a>
            <div className="pcb-note">
              <CircuitBoard size={22} />
              <p>
                {t(
                  bi(
                    "Carrier V1.1 · Design available. Fabrication, assembly and electrical validation pending.",
                    "Carrier V1.1 · Diseño disponible. Fabricación, montaje y validación eléctrica pendientes.",
                  ),
                )}
              </p>
            </div>
          </div>
          <dl className="spec-table">
            <div>
              <dt>{t(bi("Compute", "Cómputo"))}</dt>
              <dd>Raspberry Pi 5</dd>
            </div>
            <div>
              <dt>{t(bi("Control target", "Control previsto"))}</dt>
              <dd>STM32F401CCU6 Black Pill</dd>
            </div>
            <div>
              <dt>{t(bi("Audio", "Audio"))}</dt>
              <dd>ReSpeaker 2-Mics Pi HAT V2.0</dd>
            </div>
            <div>
              <dt>{t(bi("Display", "Pantalla"))}</dt>
              <dd>3.5″ · 480 × 320 · SPI</dd>
            </div>
            <div>
              <dt>{t(bi("Camera", "Cámara"))}</dt>
              <dd>Arducam OV5647 · CSI</dd>
            </div>
            <div>
              <dt>{t(bi("Actuation target", "Actuación prevista"))}</dt>
              <dd>MG996R · PWM</dd>
            </div>
            <div>
              <dt>Carrier V1.1</dt>
              <dd>100 × 92 mm · KiCad · 2 {t(bi("layers", "capas"))}</dd>
            </div>
            <div>
              <dt>{t(bi("Model geometry", "Geometría"))}</dt>
              <dd>103,446 {t(bi("triangles", "triángulos"))} · GLB V23</dd>
            </div>
          </dl>
        </section>
        <section className="about section shell" id="about">
          <div className="eyebrow">
            06 / {t(bi("BUILT OUT OF CURIOSITY", "CREADO POR CURIOSIDAD"))}
          </div>
          <h2>
            {t(bi("What if technology", "¿Y si la tecnología"))}
            <br />
            <span>
              {t(bi("felt a little more alive?", "se sintiera más viva?"))}
            </span>
          </h2>
          <div className="about-bottom">
            <div>
              <p>
                {t(
                  bi(
                    "C.U.T.Y explores what happens when a conversational AI has a physical presence. A voice becomes a character; a camera becomes eye contact; embedded electronics give that character a place in the real world.",
                    "C.U.T.Y explora qué pasa cuando una IA conversacional tiene presencia física. Una voz se vuelve personaje; una cámara, contacto visual; la electrónica le da un lugar en el mundo real.",
                  ),
                )}
              </p>
              <p>
                {t(
                  bi(
                    "The challenge is integration: reliable audio, smooth visual feedback and a clear boundary between high-level behavior and real-time control. Next comes sustained physical validation, carrier fabrication and safe motion firmware.",
                    "El reto es la integración: audio confiable, respuesta visual fluida y separación entre comportamiento y control en tiempo real. Siguen la validación sostenida, fabricación de carrier y firmware seguro.",
                  ),
                )}
              </p>
            </div>
            <a
              href={repo}
              target="_blank"
              rel="noreferrer"
              className="button primary"
            >
              {t(bi("Follow the build", "Sigue el desarrollo"))}
              <Github size={18} />
            </a>
          </div>
        </section>
      </main>
      <footer className="footer shell">
        <a className="wordmark" href="#">
          C.U.T.Y<span className="title-period">.</span>
        </a>
        <p>
          {t(
            bi(
              "Independent engineering. Open by design.",
              "Ingeniería independiente. Abierto por diseño.",
            ),
          )}
        </p>
        <a href="#main">
          {t(bi("Back to top", "Volver arriba"))}
          <ArrowDown size={15} className="up-arrow" />
        </a>
      </footer>
    </>
  );
}

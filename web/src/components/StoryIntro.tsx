import { lazy, Suspense, useEffect, useMemo, useRef } from "react";
import { ArrowDown, ArrowUpRight, Github } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { bi, repo } from "../data/project";
import { useLocale } from "../state/Locale";
import { createStoryMotion } from "../viewer/storyMotion";
import { useMedia } from "../state/useMedia";

const RobotViewer = lazy(() => import("../viewer/RobotViewer"));
gsap.registerPlugin(ScrollTrigger);

export default function StoryIntro() {
  const { t } = useLocale();
  const root = useRef<HTMLElement>(null);
  const motion = useMemo(() => createStoryMotion(), []);
  const desktop = useMedia("(min-width: 901px)");
  useEffect(() => {
    const match = gsap.matchMedia();
    match.add(
      "(min-width: 901px) and (prefers-reduced-motion: no-preference)",
      () => {
        const timeline = gsap.timeline({
          scrollTrigger: {
            trigger: root.current,
            start: "top top",
            end: "bottom bottom",
            scrub: 0.7,
            onUpdate: (self) => motion.setProgress(self.progress),
          },
        });
        timeline
          .to(".story-word", { y: -110, opacity: 0.12, ease: "none" }, 0)
          .to(".intro-chapter", { y: -65, autoAlpha: 0, duration: 0.35 }, 0.1)
          .fromTo(
            ".companion-chapter",
            { y: 65, autoAlpha: 0 },
            { y: 0, autoAlpha: 1, duration: 0.35 },
            0.45,
          )
          .to(".story-progress i", { scaleX: 1, ease: "none", duration: 1 }, 0);
        return () => {
          motion.setProgress(0);
        };
      },
      root,
    );
    return () => match.revert();
  }, [motion]);

  return (
    <section
      className="story-intro"
      ref={root}
      aria-label={t(bi("Meet C.U.T.Y.", "Conoce a C.U.T.Y."))}
    >
      <div className="story-sticky">
        <div className="story-topline">
          <span>01—02 / {t(bi("MEET C.U.T.Y.", "CONOCE A C.U.T.Y."))}</span>
          <span>
            {t(
              bi(
                "INDEPENDENT ROBOTICS PROJECT",
                "PROYECTO INDEPENDIENTE DE ROBÓTICA",
              ),
            )}
          </span>
        </div>
        <h1 className="story-word" aria-label="C.U.T.Y.">
          C.U.T.Y<span>.</span>
        </h1>
        <div className="story-layout shell">
          <div className="story-copy">
            <article className="intro-chapter">
              <p className="hero-subtitle">Cute Utility That Yaps</p>
              <h2>
                {t(bi("A little body.", "Un pequeño cuerpo."))}
                <br />
                <em>{t(bi("A curious mind.", "Una mente curiosa."))}</em>
              </h2>
              <p className="hero-description">
                {t(
                  bi(
                    "An expressive desktop companion exploring multimodal AI, computer vision and embedded systems. A small robot. A very human idea.",
                    "Un compañero de escritorio expresivo que explora IA multimodal, visión artificial y sistemas embebidos. Un robot pequeño. Una idea muy humana.",
                  ),
                )}
              </p>
              <div className="hero-buttons">
                <a className="button primary" href="#explorer">
                  {t(bi("Explore the Robot", "Explorar el robot"))}
                  <ArrowUpRight size={17} />
                </a>
                <a className="text-link" href="#architecture">
                  {t(bi("Technical Architecture", "Arquitectura técnica"))}
                  <ArrowUpRight size={16} />
                </a>
              </div>
              <a
                className="text-link hero-source"
                href={repo}
                target="_blank"
                rel="noreferrer"
              >
                <Github size={15} />
                {t(bi("View on GitHub", "Ver en GitHub"))}
              </a>
            </article>
            <article className="companion-chapter" id="companion">
              <div className="eyebrow">
                02 / {t(bi("MEET YOUR COMPANION", "CONOCE A TU COMPAÑERO"))}
              </div>
              <h2>
                {t(bi("A presence.", "Una presencia."))}
                <br />
                <em>{t(bi("With personality.", "Con personalidad."))}</em>
              </h2>
              <p className="hero-description">
                {t(
                  bi(
                    "A voice to talk with. Eyes that follow a face. Expressions that give code a character. This is the meeting point of software and a physical presence.",
                    "Una voz para conversar. Ojos que siguen una cara. Expresiones que dan carácter al código. Aquí se encuentran el software y la presencia física.",
                  ),
                )}
              </p>
              <div className="companion-notes">
                <span>
                  01 /{" "}
                  {t(
                    bi(
                      "Voice conversation tested on Pi",
                      "Conversación probada en la Pi",
                    ),
                  )}
                </span>
                <span>
                  02 /{" "}
                  {t(
                    bi(
                      "Vision & expression code developed",
                      "Visión y expresiones desarrolladas",
                    ),
                  )}
                </span>
                <span>
                  03 /{" "}
                  {t(
                    bi(
                      "Physical motion still planned",
                      "Movimiento físico aún planeado",
                    ),
                  )}
                </span>
              </div>
              <a className="text-link" href="#hardware-explorer">
                {t(bi("Go beneath the shell", "Explora bajo la carcasa"))}
                <ArrowUpRight size={17} />
              </a>
            </article>
          </div>
          <div className="story-stage">
            <div className="stage-halo" aria-hidden="true" />
            <Suspense
              fallback={
                <div className="placeholder" role="status">
                  {t(bi("Loading explorer…", "Cargando explorador…"))}
                </div>
              }
            >
              <RobotViewer motion={desktop ? motion : undefined} />
            </Suspense>
          </div>
        </div>
        <div className="story-bottom shell">
          <span>
            <ArrowDown size={14} />
            {t(bi("SCROLL TO DISCOVER", "DESPLAZA PARA DESCUBRIR"))}
          </span>
          <span>
            {t(
              bi(
                "REAL V17 ASSEMBLY · OFFLINE EXPERIENCE",
                "ENSAMBLAJE V17 REAL · EXPERIENCIA LOCAL",
              ),
            )}
          </span>
          <div className="story-progress">
            <i />
          </div>
        </div>
      </div>
    </section>
  );
}

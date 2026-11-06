import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { useLocale } from "../state/Locale";
import { bi } from "../data/project";
import { useMedia } from "../state/useMedia";
export default function IntroSequence({
  replay = false,
}: {
  replay?: boolean;
}) {
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [visible, setVisible] = useState(
    () => replay || (!window.location.hash && !reduced),
  );
  const root = useRef<HTMLDivElement>(null);
  const { t } = useLocale();
  useEffect(() => {
    if (!visible) return;
    const overflow = document.body.style.overflow;
    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    document.body.style.overflow = "hidden";
    const focusFrame = requestAnimationFrame(() =>
      root.current
        ?.querySelector<HTMLButtonElement>("button")
        ?.focus({ preventScroll: true }),
    );
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setVisible(false);
      }
      if (event.key === "Tab") {
        event.preventDefault();
        root.current?.querySelector<HTMLButtonElement>("button")?.focus();
      }
    };
    window.addEventListener("keydown", key);
    const ctx = gsap.context(() => {
      if (reduced) return;
      const timeline = gsap.timeline({ onComplete: () => setVisible(false) });
      timeline
        .fromTo(
          ".intro-letter",
          { yPercent: 130, rotate: 8 },
          {
            yPercent: 0,
            rotate: 0,
            duration: 0.85,
            stagger: 0.09,
            ease: "power4.out",
          },
        )
        .fromTo(
          ".intro-expansion span",
          { opacity: 0, y: 15 },
          { opacity: 1, y: 0, stagger: 0.14, duration: 0.35 },
          0.7,
        )
        .to(
          ".intro-rule",
          { scaleX: 1, duration: 1.15, ease: "power2.inOut" },
          0.65,
        )
        .to(
          ".intro-word",
          {
            letterSpacing: ".015em",
            scale: 1.035,
            duration: 0.55,
            ease: "power2.inOut",
          },
          1.7,
        )
        .to(
          root.current,
          {
            clipPath: "inset(0 0 100% 0)",
            duration: 0.75,
            ease: "power3.inOut",
          },
          2.35,
        );
    }, root);
    return () => {
      cancelAnimationFrame(focusFrame);
      window.removeEventListener("keydown", key);
      ctx.revert();
      document.body.style.overflow = overflow;
      if (previousFocus?.isConnected)
        previousFocus.focus({ preventScroll: true });
      requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    };
  }, [visible, reduced]);
  if (!visible) return null;
  return (
    <div
      className={`intro-sequence${reduced ? " is-static" : ""}`}
      ref={root}
      role="dialog"
      aria-modal="true"
      aria-label={t(bi("C.U.T.Y. introduction", "Introducción C.U.T.Y."))}
    >
      <div className="intro-top">
        <span>ENGINEERED TO CONNECT.</span>
        <span>V17 / NIDO</span>
      </div>
      <div className="intro-center">
        <div className="intro-word" aria-label="C.U.T.Y.">
          {"CUTY".split("").map((l, i) => (
            <span className="intro-mask" key={i}>
              <span className="intro-letter">
                {l}
                <i>.</i>
              </span>
            </span>
          ))}
        </div>
        <div className="intro-expansion">
          {["CUTE", "UTILITY", "THAT", "YAPS"].map((w) => (
            <span key={w}>{w}</span>
          ))}
        </div>
        <div className="intro-rule" />
      </div>
      <div className="intro-bottom">
        <span>
          {t(bi("A personality taking shape.", "Una personalidad toma forma."))}
        </span>
        <button
          aria-label={t(bi("Skip intro", "Saltar intro"))}
          onClick={() => setVisible(false)}
        >
          {t(bi("Skip intro", "Saltar intro"))} ↗
        </button>
      </div>
    </div>
  );
}

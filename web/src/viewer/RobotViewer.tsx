import {
  Component,
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  Box,
  LoaderCircle,
  Pause,
  Play,
  RotateCcw,
  ScanLine,
  ZoomIn,
  ZoomOut,
  X,
  Move3D,
} from "lucide-react";
import { useLocale } from "../state/Locale";
import { useMedia } from "../state/useMedia";
import { bi } from "../data/project";
import type { CameraView } from "./model";
import { modelInfo } from "../data/model";
import DisplayControls from "../components/DisplayControls";
import type { StoryMotion } from "./storyMotion";
import { emptyShot, resolveShot } from "./choreography";
import type { AssemblyView, PoseDemo } from "./assembly";
const Scene = lazy(() => import("./Scene"));
class ModelBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { error: boolean }
> {
  state = { error: false };
  static getDerivedStateFromError() {
    return { error: true };
  }
  render() {
    return this.state.error ? this.props.fallback : this.props.children;
  }
}
const viewLabels = {
  front: bi("Front", "Frente"),
  side: bi("Side", "Lateral"),
  top: bi("Top", "Superior"),
  iso: bi("Isometric", "Isométrica"),
  display: bi("LCD", "LCD"),
};
export default function RobotViewer({ motion }: { motion: StoryMotion }) {
  const { t } = useLocale();
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const compact = useMedia("(max-width: 900px)");
  const [auto, setAuto] = useState(false),
    [view, setView] = useState<CameraView>("iso");
  const [wireframe, setWireframe] = useState(false),
    [reset, setReset] = useState(0);
  const [loaded, setLoaded] = useState(false),
    [active, setActive] = useState(true);
  const [zoom, setZoom] = useState(0),
    [exploring, setExploring] = useState(false);
  const [assemblyView, setAssemblyView] = useState<AssemblyView>("assembled");
  const [pose, setPose] = useState<PoseDemo>("none");
  const layer = useRef<HTMLDivElement>(null),
    open = useRef<HTMLButtonElement>(null),
    close = useRef<HTMLButtonElement>(null);
  const onLoaded = useCallback(() => setLoaded(true), []);
  const finish = useCallback(() => {
    setExploring(false);
    setAuto(false);
    setAssemblyView("assembled");
    setPose("none");
    motion.follow(true);
    open.current?.focus();
  }, [motion]);
  useEffect(() => {
    const shot = emptyShot();
    const update = () => {
      resolveShot(motion.progress, compact, reduced, shot);
      if (layer.current) {
        layer.current.style.opacity = String(exploring ? 1 : shot.visible);
        layer.current.dataset.chapter = String(Math.round(motion.progress));
      }
      if (open.current) open.current.hidden = shot.visible < 0.02;
      setActive(!document.hidden && (exploring || shot.visible > 0.01));
    };
    update();
    const unsubscribe = motion.subscribe(update);
    document.addEventListener("visibilitychange", update);
    return () => {
      unsubscribe();
      document.removeEventListener("visibilitychange", update);
    };
  }, [motion, compact, reduced, exploring]);
  useEffect(() => {
    if (!exploring) return;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    close.current?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape") finish();
      if (event.key === "Tab") {
        const elements = Array.from(
          document.querySelectorAll<HTMLElement>(
            '.explore-close, .explore-panel button:not(:disabled), .explore-panel select, .scene-layer [tabindex="0"]',
          ),
        );
        const first = elements[0],
          last = elements.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener("keydown", key);
    return () => {
      document.body.style.overflow = overflow;
      window.removeEventListener("keydown", key);
    };
  }, [exploring, finish]);
  const resetCamera = () => {
    setView("iso");
    setZoom(0);
    setReset((value) => value + 1);
  };
  const fallback = (
    <div className="viewer-message" role="alert">
      <Box size={30} />
      <h3>
        {t(
          bi("The model could not be loaded.", "No se pudo cargar el modelo."),
        )}
      </h3>
      <p>
        {t(
          bi(
            "Check WebGL support. The real assembly belongs at:",
            "Revisa WebGL. El ensamblaje real debe estar en:",
          ),
        )}
      </p>
      <code>web/public/models/cuty.glb</code>
      <button
        className="button secondary"
        onClick={() => window.location.reload()}
      >
        {t(bi("Reload viewer", "Recargar visor"))}
      </button>
    </div>
  );
  return (
    <div className={`persistent-viewer ${exploring ? "is-exploring" : ""}`}>
      <div className="scene-layer" ref={layer}>
        <div
          className="canvas-wrap"
          tabIndex={exploring ? 0 : -1}
          role="group"
          aria-label={t(
            bi("C.U.T.Y. V17 3D assembly", "Ensamblaje 3D C.U.T.Y. V17"),
          )}
          onKeyDown={(event) => {
            if (!exploring) return;
            if (event.key === "Home") {
              event.preventDefault();
              resetCamera();
            }
            if (event.key === "+" || event.key === "=")
              setZoom((z) => Math.min(3, z + 1));
            if (event.key === "-") setZoom((z) => Math.max(-3, z - 1));
          }}
        >
          <ModelBoundary fallback={fallback}>
            <Suspense fallback={null}>
              <Scene
                assemblyView={assemblyView}
                pose={pose}
                view={view}
                reset={reset}
                zoom={zoom}
                autoRotate={auto && !reduced}
                wireframe={wireframe}
                reduced={reduced}
                active={active}
                exploring={exploring}
                motion={motion}
                onLoaded={onLoaded}
              />
            </Suspense>
            {!loaded && (
              <div className="loading-model" role="status">
                <LoaderCircle size={16} className="spin" />
                {t(bi("Loading real GLB…", "Cargando GLB real…"))}
              </div>
            )}
          </ModelBoundary>
        </div>
      </div>
      {!exploring && (
        <button
          className="explore-launch"
          ref={open}
          onClick={() => {
            motion.follow(false);
            resetCamera();
            setExploring(true);
          }}
        >
          <Move3D size={18} />
          {t(bi("Explore in 3D", "Explorar en 3D"))}
        </button>
      )}
      {exploring && (
        <div
          className="exploration-ui"
          role="dialog"
          aria-modal="true"
          aria-label={t(
            bi("Interactive robot explorer", "Explorador interactivo"),
          )}
        >
          <button ref={close} className="explore-close" onClick={finish}>
            <X size={18} />
            {t(bi("Back to the story", "Volver a la historia"))}
          </button>
          <div className="explore-panel">
            <div className="viewer-top">
              <span>
                {t(
                  bi(
                    `REAL ASSEMBLY / ${modelInfo.revision}`,
                    `ENSAMBLAJE REAL / ${modelInfo.revision}`,
                  ),
                )}
              </span>
              <span>
                {t(
                  bi(
                    "Drag to orbit · pinch to zoom",
                    "Arrastra para girar · pellizca para zoom",
                  ),
                )}
              </span>
            </div>
            <div className="viewer-toolbar">
              <div className="view-presets">
                {(Object.keys(viewLabels) as CameraView[]).map((key) => (
                  <button
                    key={key}
                    aria-pressed={view === key}
                    onClick={() => {
                      setView(key);
                      setReset((v) => v + 1);
                    }}
                  >
                    {t(viewLabels[key])}
                  </button>
                ))}
              </div>
              <div className="viewer-actions">
                <button
                  className="icon-button"
                  aria-label={t(bi("Zoom in", "Acercar"))}
                  disabled={zoom === 3}
                  onClick={() => setZoom((z) => Math.min(3, z + 1))}
                >
                  <ZoomIn size={18} />
                </button>
                <button
                  className="icon-button"
                  aria-label={t(bi("Zoom out", "Alejar"))}
                  disabled={zoom === -3}
                  onClick={() => setZoom((z) => Math.max(-3, z - 1))}
                >
                  <ZoomOut size={18} />
                </button>
                <button
                  className="icon-button"
                  aria-label={t(bi("Reset camera", "Restablecer cámara"))}
                  onClick={resetCamera}
                >
                  <RotateCcw size={18} />
                </button>
                <button
                  className="icon-button"
                  aria-label={t(bi("Wireframe", "Malla alámbrica"))}
                  aria-pressed={wireframe}
                  onClick={() => setWireframe((v) => !v)}
                >
                  <ScanLine size={18} />
                </button>
                <button
                  className="icon-button"
                  disabled={reduced}
                  aria-label={t(bi("Auto-rotate", "Autorrotación"))}
                  aria-pressed={auto && !reduced}
                  onClick={() => setAuto((v) => !v)}
                >
                  {auto ? <Pause size={18} /> : <Play size={18} />}
                </button>
              </div>
            </div>
            <DisplayControls />
            <div
              className="assembly-controls"
              aria-label={t(bi("Assembly display", "Vista de ensamblaje"))}
            >
              {(["assembled", "interior", "exploded"] as const).map(
                (value, index) => (
                  <button
                    key={value}
                    aria-pressed={assemblyView === value}
                    onClick={() => {
                      setAssemblyView(value);
                      setPose("none");
                    }}
                  >
                    {t(
                      [
                        bi("Assembled", "Ensamblado"),
                        bi("Inside", "Interior"),
                        bi("Exploded view", "Vista explotada"),
                      ][index],
                    )}
                  </button>
                ),
              )}
              <button
                disabled={reduced}
                aria-pressed={pose === "wave"}
                onClick={() => {
                  setAssemblyView("assembled");
                  setPose((p) => (p === "wave" ? "none" : "wave"));
                }}
              >
                {t(bi("Wave demo", "Demo de saludo"))}
              </button>
              <button
                disabled={reduced}
                aria-pressed={pose === "look"}
                onClick={() => {
                  setAssemblyView("assembled");
                  setPose((p) => (p === "look" ? "none" : "look"));
                }}
              >
                {t(bi("Look demo", "Demo de giro"))}
              </button>
            </div>
            <p className="simulation-note">
              {t(
                bi(
                  "Named CAD parts · visual simulation only. No motors are controlled.",
                  "Piezas CAD con nombre · solo simulación visual. No controla motores.",
                ),
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

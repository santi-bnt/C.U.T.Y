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
} from "lucide-react";
import { useLocale } from "../state/Locale";
import { useMedia } from "../state/useMedia";
import { bi } from "../data/project";
import type { CameraView } from "./model";
import { modelInfo } from "../data/model";
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
};
export default function RobotViewer() {
  const { t } = useLocale();
  const reduced = useMedia("(prefers-reduced-motion: reduce)");
  const [auto, setAuto] = useState(false);
  const [view, setView] = useState<CameraView>("iso");
  const [wireframe, setWireframe] = useState(false);
  const [reset, setReset] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [active, setActive] = useState(true);
  const [zoom, setZoom] = useState(0);
  const frame = useRef<HTMLDivElement>(null);
  const onLoaded = useCallback(() => setLoaded(true), []);
  useEffect(() => {
    const element = frame.current;
    if (!element) return;
    let visible = true;
    const update = () => setActive(visible && !document.hidden);
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      update();
    });
    observer.observe(element);
    document.addEventListener("visibilitychange", update);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", update);
    };
  }, []);
  const resetCamera = () => {
    setView("iso");
    setZoom(0);
    setReset((value) => value + 1);
  };
  const fallback = (
    <div className="viewer-message" role="alert">
      <Box size={36} />
      <h3>
        {t(
          bi("The model could not be loaded.", "No se pudo cargar el modelo."),
        )}
      </h3>
      <p>
        {t(
          bi(
            "Check WebGL support and place the real GLB at:",
            "Comprueba WebGL y coloca el GLB real en:",
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
    <div id="explorer" className="explorer" ref={frame}>
      <div className="viewer-top">
        <span>
          <span className="status-dot" />
          {t(bi("REAL ASSEMBLY / V23", "ENSAMBLAJE REAL / V23"))}
        </span>
        <span>GLB · {modelInfo.triangles.toLocaleString("en-US")} △</span>
      </div>
      <div
        className="canvas-wrap"
        tabIndex={0}
        role="group"
        aria-label={t(
          bi(
            "3D robot viewer. Use the view and zoom buttons below, or drag to orbit and pinch to zoom.",
            "Visor 3D. Usa los botones de vista y zoom, o arrastra para girar y pellizca para acercar.",
          ),
        )}
        onKeyDown={(event) => {
          if (event.key === "Home") {
            event.preventDefault();
            resetCamera();
          }
          if (event.key === "+" || event.key === "=")
            setZoom((z) => Math.min(3, z + 1));
          if (event.key === "-") setZoom((z) => Math.max(-3, z - 1));
        }}
      >
        <div className="orbit-ring ring-one" />
        <div className="orbit-ring ring-two" />
        <ModelBoundary fallback={fallback}>
          <Suspense
            fallback={
              <div className="viewer-message">
                <LoaderCircle className="spin" />
                {t(bi("Preparing 3D explorer…", "Preparando explorador 3D…"))}
              </div>
            }
          >
            <Scene
              view={view}
              reset={reset}
              zoom={zoom}
              autoRotate={auto && !reduced}
              wireframe={wireframe}
              reduced={reduced}
              active={active}
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
        <div className="viewer-coordinate">
          Y ↑<br />
          <span>X / Z</span>
        </div>
        <div className="viewer-hint">
          {t(
            bi(
              "DRAG TO ORBIT · SCROLL TO ZOOM",
              "ARRASTRA PARA GIRAR · DESPLAZA PARA ZOOM",
            ),
          )}
        </div>
      </div>
      <div className="viewer-toolbar">
        <div
          className="view-presets"
          aria-label={t(bi("Camera views", "Vistas de cámara"))}
        >
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
            title={t(bi("Zoom in", "Acercar"))}
            aria-label={t(bi("Zoom in", "Acercar"))}
            onClick={() => setZoom((z) => Math.min(3, z + 1))}
            disabled={zoom === 3}
          >
            <ZoomIn size={17} />
          </button>
          <button
            className="icon-button"
            title={t(bi("Zoom out", "Alejar"))}
            aria-label={t(bi("Zoom out", "Alejar"))}
            onClick={() => setZoom((z) => Math.max(-3, z - 1))}
            disabled={zoom === -3}
          >
            <ZoomOut size={17} />
          </button>
          <button
            className="icon-button"
            aria-label={t(bi("Reset camera", "Restablecer cámara"))}
            title={t(bi("Reset camera", "Restablecer cámara"))}
            onClick={resetCamera}
          >
            <RotateCcw size={17} />
          </button>
          <button
            className="icon-button"
            aria-pressed={wireframe}
            aria-label={t(bi("Wireframe", "Malla alámbrica"))}
            title={t(bi("Wireframe", "Malla alámbrica"))}
            onClick={() => setWireframe((v) => !v)}
          >
            <ScanLine size={17} />
          </button>
          <button
            className="icon-button"
            disabled={reduced}
            aria-pressed={auto && !reduced}
            aria-label={t(bi("Auto-rotate", "Autorrotación"))}
            title={t(
              bi(
                "Auto-rotate (disabled for reduced motion)",
                "Autorrotación (desactivada con movimiento reducido)",
              ),
            )}
            onClick={() => setAuto((v) => !v)}
          >
            {auto && !reduced ? <Pause size={17} /> : <Play size={17} />}
          </button>
        </div>
      </div>
    </div>
  );
}

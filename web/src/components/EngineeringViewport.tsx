import {
  Component,
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { bi } from "../data/project";
import { useLocale } from "../state/Locale";
import type { WireFilter } from "../data/engineering";
const Scene = lazy(() => import("../viewer/EngineeringScene"));
export interface EngineeringProps {
  mode: "pcb" | "wiring";
  selected: string | null;
  onSelect: (id: string) => void;
  hover?: string | null;
  onHover?: (id: string | null) => void;
  filter?: WireFilter;
  view?: "front" | "back" | "iso";
  zoom?: number;
  reset?: number;
}
class Boundary extends Component<
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
export default function EngineeringViewport(props: EngineeringProps) {
  const root = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(false),
    [active, setActive] = useState(true);
  const { t } = useLocale();
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setActive(entry.isIntersecting && !document.hidden);
        if (entry.isIntersecting) setSeen(true);
      },
      { rootMargin: "100px" },
    );
    if (root.current) observer.observe(root.current);
    const visible = () => setActive(!document.hidden);
    document.addEventListener("visibilitychange", visible);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", visible);
    };
  }, []);
  const fallback = (
    <div className="engineering-loading" role="status">
      {t(
        bi(
          "3D preview unavailable. The source layout and connection tables remain accessible.",
          "Vista 3D no disponible. El diseño y las tablas de conexiones siguen accesibles.",
        ),
      )}
    </div>
  );
  return (
    <div
      className={`engineering-viewport ${props.mode}`}
      ref={root}
      data-mode={props.mode}
      aria-label={t(
        bi("Interactive CAD reference", "Referencia CAD interactiva"),
      )}
    >
      <Boundary fallback={fallback}>
        <Suspense
          fallback={
            <div className="engineering-loading" role="status">
              {t(bi("Loading supplied CAD…", "Cargando CAD recibido…"))}
            </div>
          }
        >
          {seen && <Scene {...props} active={active} />}
        </Suspense>
      </Boundary>
    </div>
  );
}

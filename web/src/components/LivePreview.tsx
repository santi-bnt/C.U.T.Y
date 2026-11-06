import { ArrowUpRight, Radio, Monitor, Unplug } from "lucide-react";
import { bi, source } from "../data/project";
import { useLocale } from "../state/Locale";
import { offlineRobot } from "../communication/robot";

export default function LivePreview() {
  const { t } = useLocale();
  const snapshot = offlineRobot.getSnapshot();
  return (
    <section className="live-section section" id="live">
      <div className="shell live-layout">
        <div>
          <div className="eyebrow">
            05 / {t(bi("C.U.T.Y. LIVE", "C.U.T.Y. EN VIVO"))}
          </div>
          <h2>
            {t(bi("A window into", "Una ventana a"))}
            <br />
            <em>{t(bi("its world.", "su mundo."))}</em>
          </h2>
          <p>
            {t(
              bi(
                "Today, an independent browser experience. Tomorrow, a window into the robot’s own display. Explore the face demo above while the physical connection is offline.",
                "Hoy, una experiencia independiente en el navegador. Después, una ventana a la pantalla del robot. Explora la demo de arriba mientras la conexión física está desconectada.",
              ),
            )}
          </p>
          <a className="button secondary" href="#intelligence">
            {t(bi("Try the face demo", "Prueba la cara"))}
            <ArrowUpRight size={17} />
          </a>
        </div>
        <div className="live-terminal" data-connection={snapshot.connection}>
          <div className="terminal-heading">
            <Radio size={16} />
            <span>C.U.T.Y / DISPLAY LINK</span>
            <span className="badge planned">
              {t(bi("OFFLINE", "DESCONECTADO"))}
            </span>
          </div>
          <div className="offline-visual" aria-hidden="true">
            <div className="signal-orbit" />
            <Monitor size={54} strokeWidth={1} />
            <Unplug size={22} />
          </div>
          <h3>
            {t(
              bi("The robot is not connected.", "El robot no está conectado."),
            )}
          </h3>
          <p>
            {t(
              bi(
                "No live camera, microphone or hardware commands. The eyes on this page are original Python-rendered demo frames.",
                "Sin cámara, micrófono ni órdenes de hardware en vivo. Los ojos de esta página son fotogramas demo del renderizador Python original.",
              ),
            )}
          </p>
          <div className="terminal-footer">
            <span>480 × 320 / RGB</span>
            <a
              className="text-link"
              href={source("raspberry/src/cuty/face")}
              target="_blank"
              rel="noreferrer"
            >
              {t(bi("Face renderer source", "Código del renderizador"))}
              <ArrowUpRight size={14} />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

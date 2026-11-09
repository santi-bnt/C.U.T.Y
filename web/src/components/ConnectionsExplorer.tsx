import { useMemo, useState } from "react";
import { Check, Clipboard, Download, Search } from "lucide-react";
import {
  matchesFilter,
  wiringStates,
  type WireFilter,
} from "../data/engineering";
import { connectionRows, wiringNodes } from "../data/operationalWiring";
import { bi } from "../data/project";
import { useLocale } from "../state/Locale";

type CategoryId =
  | "all"
  | "pi"
  | "audio"
  | "display"
  | "camera"
  | "stm"
  | "servos"
  | "power";

const categories: { id: CategoryId; label: ReturnType<typeof bi> }[] = [
  { id: "all", label: bi("All connections", "Todas las conexiones") },
  { id: "pi", label: bi("Raspberry Pi 5", "Raspberry Pi 5") },
  { id: "audio", label: bi("ReSpeaker 2-Mics HAT", "ReSpeaker 2-Mics HAT") },
  { id: "display", label: bi("Waveshare 3.5″ display", "Pantalla Waveshare 3.5″") },
  { id: "camera", label: bi("Arducam camera", "Cámara Arducam") },
  { id: "stm", label: bi("STM32F401", "STM32F401") },
  { id: "servos", label: bi("Servo motors", "Servomotores") },
  { id: "power", label: bi("Power & battery", "Potencia y batería") },
];

function inCategory(
  row: (typeof connectionRows)[number],
  category: CategoryId,
) {
  if (category === "all") return true;
  if (category === "power")
    return (
      row.id.startsWith("battery-") ||
      row.id.startsWith("servo-supply") ||
      row.id.startsWith("servo-ground") ||
      row.id.startsWith("common-") ||
      row.id === "pi-power" ||
      row.id === "pi-battery"
    );
  return row.from === category || row.to === category;
}

function physicalPin(pin: string) {
  const match = pin.match(/\bPi(?:\s+physical)?\s+(\d+)\b/i);
  if (match) return match[1];
  if (/\bTBD\b|por confirmar|por asignar/i.test(pin)) return "TBD";
  return "—";
}

function csvCell(value: string) {
  return `"${value.replaceAll('"', '""')}"`;
}

function ConnectionsTable({
  rows,
  labels,
}: {
  rows: typeof connectionRows;
  labels: {
    physicalPin: string;
    gpio: string;
    source: string;
    destination: string;
    signalVoltage: string;
    status: string;
    details: string;
    copy: string;
    copied: string;
    evidence: string;
    sourcePin: string;
    target: string;
  };
}) {
  const { t } = useLocale();
  const [copied, setCopied] = useState<string | null>(null);
  const copyRow = async (row: (typeof connectionRows)[number]) => {
    const text = `${row.pin} -> ${row.destination} | ${row.gpio} | ${row.net} | ${row.voltage}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(row.id);
      window.setTimeout(() => setCopied((current) => current === row.id ? null : current), 1600);
    } catch {
      setCopied(null);
    }
  };
  return (
    <div className="connections-table-wrap">
      <table className="connections-table">
        <thead>
          <tr>
            <th>{labels.physicalPin}</th>
            <th>{labels.gpio}</th>
            <th>{labels.source}</th>
            <th>{labels.destination}</th>
            <th>{labels.signalVoltage}</th>
            <th>{labels.status}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const pendingPin =
              row.status === "proposed" &&
              /\bTBD\b|por confirmar|por asignar/i.test(
                `${row.pin} ${row.destination} ${row.net}`,
              );
            return (
              <tr key={row.id}>
                <td data-label={labels.physicalPin}>
                  <span className={`physical-pin ${physicalPin(row.pin) === "TBD" ? "pending" : ""}`}>
                    {physicalPin(row.pin)}
                  </span>
                </td>
                <td data-label={labels.gpio}>{row.gpio}</td>
                <td data-label={labels.source}>{row.pin}</td>
                <td data-label={labels.destination}>{row.destination}</td>
                <td data-label={labels.signalVoltage}>
                  <strong>{row.net}</strong>
                  <small>{row.voltage}</small>
                </td>
                <td data-label={labels.status}>
                  <span className={`connection-status ${row.status}`}>
                    {t(wiringStates[row.status])}
                  </span>
                  {pendingPin && (
                    <small className="pending-note">
                      {t(bi("Pin assignment pending", "Asignación de pin pendiente"))}
                    </small>
                  )}
                  <details className="connection-row-details">
                    <summary>{labels.details}</summary>
                    <div className="connection-details-content">
                      <p><b>{labels.sourcePin}:</b> {row.pin}</p>
                      <p><b>{labels.target}:</b> {row.destination}</p>
                      <p><b>{labels.gpio}:</b> {row.gpio}</p>
                      <p><b>{labels.signalVoltage}:</b> {row.net} · {row.voltage}</p>
                      <div className="connection-detail-actions">
                        <button type="button" onClick={() => void copyRow(row)}>
                          {copied === row.id ? <Check size={14} /> : <Clipboard size={14} />}
                          {copied === row.id ? labels.copied : labels.copy}
                        </button>
                        <a href={row.source} target="_blank" rel="noreferrer">{labels.evidence} ↗</a>
                      </div>
                    </div>
                  </details>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {rows.length === 0 && (
        <div className="connections-empty" role="status">
          {t(bi("No connections match this search.", "No hay conexiones que coincidan con la búsqueda."))}
        </div>
      )}
    </div>
  );
}

export default function ConnectionsExplorer({ filter }: { filter: WireFilter }) {
  const { t } = useLocale();
  const [category, setCategory] = useState<CategoryId>("display");
  const [query, setQuery] = useState("");
  const labelFor = (id: string) => wiringNodes.find((node) => node.id === id)?.label ?? id;
  const categoryRows = useMemo(
    () => connectionRows.filter((row) => inCategory(row, category)),
    [category],
  );
  const rows = useMemo(
    () => categoryRows.filter((row) => {
      if (!matchesFilter(row, filter)) return false;
      const searchable = [
        row.id, row.pin, row.destination, row.gpio, row.net, row.voltage,
        row.status, labelFor(row.from), labelFor(row.to),
      ].join(" ").toLocaleLowerCase();
      return searchable.includes(query.trim().toLocaleLowerCase());
    }),
    [categoryRows, filter, query],
  );
  const exportCsv = () => {
    const headings = ["Physical Pin", "GPIO / BCM", "Source", "Destination", "Signal", "Voltage", "Verification Status", "Evidence"];
    const lines = rows.map((row) => [
      physicalPin(row.pin), row.gpio, row.pin, row.destination, row.net,
      row.voltage, row.status, row.source,
    ]);
    const csv = [headings, ...lines].map((line) => line.map(csvCell).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `cuty-connections-${category}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  const labels = {
    physicalPin: t(bi("Physical pin", "Pin físico")),
    gpio: t(bi("GPIO / BCM", "GPIO / BCM")),
    source: t(bi("Source", "Origen")),
    destination: t(bi("Destination", "Destino")),
    signalVoltage: t(bi("Signal / voltage", "Señal / voltaje")),
    status: t(bi("Verification status", "Estado de verificación")),
    details: t(bi("Details", "Detalles")),
    copy: t(bi("Copy mapping", "Copiar conexión")),
    copied: t(bi("Copied", "Copiado")),
    evidence: t(bi("Technical evidence", "Evidencia técnica")),
    sourcePin: t(bi("Source pin", "Pin de origen")),
    target: t(bi("Destination", "Destino")),
  };

  return (
    <section className="connections-explorer" aria-labelledby="connections-title">
      <header className="connections-explorer-header">
        <div>
          <span className="connections-eyebrow">{t(bi("SOURCE-BACKED PINOUT", "PINES CON FUENTE TÉCNICA"))}</span>
          <h3 id="connections-title">{t(bi("Connections explorer", "Explorador de conexiones"))}</h3>
          <p>{t(bi("Browse the documented hookups by component. Physical header pins and BCM numbering are kept in separate columns.", "Consulta conexiones por componente. Los pines físicos del header y la numeración BCM aparecen por separado."))}</p>
        </div>
        <div className="connections-explorer-actions">
          <span className="connections-total">39 {t(bi("records", "registros"))}</span>
          <button className="connections-export" type="button" onClick={exportCsv}>
            <Download size={15} /> {t(bi("Export CSV", "Exportar CSV"))}
          </button>
        </div>
      </header>
      <div className="connections-explorer-toolbar">
        <label className="connections-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">{t(bi("Search connections", "Buscar conexiones"))}</span>
          <input
            type="search"
            aria-label={t(bi("Search connections", "Buscar conexiones"))}
            placeholder={t(bi("Search pin, BCM, signal or component…", "Buscar pin, BCM, señal o componente…"))}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <p className="connections-result-count" aria-live="polite">
          {rows.length} / {categoryRows.length} {t(bi("connections", "conexiones"))}
        </p>
        <label className="connections-mobile-selector">
          <span>{t(bi("Component", "Componente"))}</span>
          <select value={category} onChange={(event) => setCategory(event.target.value as CategoryId)}>
            {categories.map((item) => (
              <option key={item.id} value={item.id}>
                {t(item.label)} ({connectionRows.filter((row) => inCategory(row, item.id)).length})
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="connections-explorer-layout">
        <nav className="component-selector" aria-label={t(bi("Filter by component", "Filtrar por componente"))}>
          {categories.map((item) => {
            const count = connectionRows.filter((row) => inCategory(row, item.id)).length;
            return (
              <button
                key={item.id}
                type="button"
                className={category === item.id ? "active" : ""}
                aria-pressed={category === item.id}
                onClick={() => setCategory(item.id)}
              >
                <span>{t(item.label)}</span><small>{count}</small>
              </button>
            );
          })}
        </nav>
        <div className="connections-explorer-results">
          <div className="connections-status-key" aria-label={t(bi("Verification states", "Estados de verificación"))}>
            {(["confirmed", "proposed", "unverified"] as const).map((status) => (
              <span key={status} className={`connection-status ${status}`}>
                {t(wiringStates[status])}
              </span>
            ))}
            <span className="pending-note">{t(bi("TBD = pin assignment pending", "TBD = asignación de pin pendiente"))}</span>
          </div>
          <ConnectionsTable rows={rows} labels={labels} />
        </div>
      </div>
    </section>
  );
}

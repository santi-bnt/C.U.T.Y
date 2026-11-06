import { useMemo, useState } from "react";
import { ArrowUpRight, Search } from "lucide-react";
import {
  carrier,
  filters,
  filterNames,
  matchesFilter,
  wiringStates,
  type WireFilter,
} from "../data/engineering";
import { bi, source } from "../data/project";
import { useLocale } from "../state/Locale";
import EngineeringViewport from "./EngineeringViewport";
import {
  connectionRows,
  wiringEdges,
  wiringNodes,
  wiringEvidence,
} from "../data/operationalWiring";

export default function WiringConnections() {
  const { t } = useLocale();
  const [selected, setSelected] = useState<string | null>(null);
  const [spatial, setSpatial] = useState(true);
  const [filter, setFilter] = useState<WireFilter>("all"),
    [query, setQuery] = useState("");
  const node = wiringNodes.find((n) => n.id === selected);
  const rows = useMemo(
    () =>
      connectionRows.filter(
        (row) =>
          (!selected || row.from === selected || row.to === selected) &&
          matchesFilter(row, filter) &&
          `${row.net} ${row.pin} ${row.destination} ${row.gpio} ${row.voltage} ${row.status}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [selected, filter, query],
  );
  const relevantEdges = wiringEdges.filter(
    (edge) =>
      filter === "all" ||
      edge.kind === filter ||
      (filter === "signals" && !["power", "ground"].includes(edge.kind)) ||
      (filter === "GPIO" && ["SPI", "I2C", "I2S", "UART"].includes(edge.kind)),
  );
  const neighbors = new Set([
    selected,
    ...relevantEdges
      .filter((e) => e.from === selected || e.to === selected)
      .flatMap((e) => [e.from, e.to]),
  ]);
  return (
    <section
      className="technical-section wiring-section ink"
      id="wiring"
      data-scene="wiring"
    >
      <div className="technical-heading">
        <span className="eyebrow">
          05 / {t(bi("WIRING & CONNECTIONS", "CABLEADO Y CONEXIONES"))}
        </span>
        <h2 className="reveal-line">
          <span>
            {t(bi("The connections matter.", "Las conexiones importan."))}
          </span>
        </h2>
        <p>
          {t(
            bi(
              "Follow the signal. Trace the power. A source-backed map of the design, with the unknowns left visible.",
              "Sigue la señal. Traza la energía. Un mapa del diseño respaldado por fuentes, con las dudas a la vista.",
            ),
          )}
        </p>
      </div>
      <div className="engineering-notice">
        <strong>
          {t(
            bi(
              "DISPLAY / AUDIO / VISION CONFIRMED / FUTURE CONTROL MARKED SEPARATELY",
              "PANTALLA / AUDIO / VISIÓN CONFIRMADOS / CONTROL FUTURO IDENTIFICADO APARTE",
            ),
          )}
        </strong>
        <span>
          {t(
            bi(
              "Display and ReSpeaker connections confirmed working together by the builder. These pin tables follow the supplied hookup list; native CAD connectors are documented separately.",
              "Pantalla y ReSpeaker confirmados funcionando juntos por el constructor. Estas tablas siguen el cableado proporcionado; los conectores CAD se documentan por separado.",
            ),
          )}
        </span>
      </div>
      <div
        className="wire-filters"
        aria-label={t(bi("Connection filters", "Filtros de conexiones"))}
      >
        {filters.map((value) => (
          <button
            key={value}
            aria-pressed={filter === value}
            onClick={() => setFilter(value)}
          >
            {t(filterNames[value])}
          </button>
        ))}
      </div>
      <div className="wiring-workspace">
        <div className="wiring-diagram-panel">
          <div className="engineering-toolbar">
            <span className="mono">
              {t(
                bi(
                  "FUNCTIONAL CONNECTIONS / SELECT A PART",
                  "CONEXIONES FUNCIONALES / SELECCIONA UNA PIEZA",
                ),
              )}
            </span>
            <button className="text-link" onClick={() => setSelected(null)}>
              {t(bi("Show all connections", "Ver todas las conexiones"))}
            </button>
          </div>
          <div className="assembly-controls">
            <button aria-pressed={spatial} onClick={() => setSpatial(true)}>
              {t(bi("3D simulation", "Simulación 3D"))}
            </button>
            <button aria-pressed={!spatial} onClick={() => setSpatial(false)}>
              {t(bi("2D overview", "Resumen 2D"))}
            </button>
          </div>
          {spatial ? (
            <>
              <EngineeringViewport
                mode="wiring"
                selected={selected}
                onSelect={setSelected}
                filter={filter}
              />
              <p className="simulation-note">
                {t(
                  bi(
                    "Orbit the actual CAD interior. Colored curves simulate electrical relationships, not physical cable routes. Ground topology remains in the table: NT1 has no dedicated CAD solid.",
                    "Gira el interior CAD real. Las curvas de color simulan relaciones eléctricas, no rutas físicas de cables. La topología de tierra sigue en la tabla: NT1 no tiene sólido CAD propio.",
                  ),
                )}
              </p>
            </>
          ) : (
            <svg
              className="wiring-diagram"
              viewBox="-20 0 1040 600"
              role="group"
              aria-label={t(
                bi(
                  "Interactive carrier electrical architecture",
                  "Arquitectura eléctrica interactiva",
                ),
              )}
            >
              <defs>
                <marker
                  id="wire-arrow"
                  markerWidth="6"
                  markerHeight="6"
                  refX="5"
                  refY="3"
                  orient="auto"
                >
                  <path d="M0,0 L6,3 L0,6Z" fill="context-stroke" />
                </marker>
              </defs>
              {relevantEdges.map((edge, index) => {
                const from = wiringNodes.find((n) => n.id === edge.from)!,
                  to = wiringNodes.find((n) => n.id === edge.to)!;
                const siblings = relevantEdges.filter(
                  (e) => e.from === edge.from && e.to === edge.to,
                );
                const order = siblings.indexOf(edge);
                const bend =
                  (order - (siblings.length - 1) / 2) * 120 +
                  (siblings.length === 1 ? (index % 2 ? 20 : -20) : 0);
                const midX = (from.x + to.x) / 2 + bend,
                  midY = (from.y + to.y) / 2 + bend;
                return (
                  <g
                    key={`${edge.from}-${edge.to}-${edge.kind}`}
                    className={`wire-edge ${edge.kind} ${edge.status} ${!selected || edge.from === selected || edge.to === selected ? "relevant" : "dimmed"}`}
                  >
                    <path
                      d={`M${from.x},${from.y} Q${midX},${midY} ${to.x},${to.y}`}
                      markerEnd="url(#wire-arrow)"
                    />
                    <title>{edge.label}</title>
                    {(filter !== "all" ||
                      (selected &&
                        (edge.from === selected || edge.to === selected))) && (
                      <text
                        x={(from.x + to.x) / 2 + bend / 2}
                        y={(from.y + to.y) / 2 + bend / 2 - 6}
                        textAnchor="middle"
                      >
                        {edge.label}
                      </text>
                    )}
                  </g>
                );
              })}
              {wiringNodes.map((n) => (
                <g
                  key={n.id}
                  className={`wire-node ${selected === n.id ? "selected" : ""} ${selected && !neighbors.has(n.id) ? "dimmed" : ""}`}
                  role="button"
                  tabIndex={0}
                  aria-label={`${t(bi("Connections for", "Conexiones de"))} ${n.label}`}
                  aria-pressed={selected === n.id}
                  onClick={() => setSelected(n.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setSelected(n.id);
                    }
                  }}
                >
                  <rect
                    x={n.x - 96}
                    y={n.y - 32}
                    width="192"
                    height="64"
                    rx="7"
                  />
                  <text x={n.x} y={n.y - 3} textAnchor="middle">
                    {n.label}
                  </text>
                  <text
                    className="node-ref"
                    x={n.x}
                    y={n.y + 18}
                    textAnchor="middle"
                  >
                    {n.refs.join(" / ") || "CSI / Pi"}
                  </text>
                </g>
              ))}
            </svg>
          )}
          <div
            className={
              spatial ? "wire-mobile-nodes spatial-parts" : "wire-mobile-nodes"
            }
          >
            {wiringNodes.map((n) => (
              <button
                key={n.id}
                aria-pressed={selected === n.id}
                onClick={() => setSelected(n.id)}
              >
                {n.label}
                <ArrowUpRight size={14} />
              </button>
            ))}
          </div>
          <div className="wire-legend">
            <span>
              <i className="power" />
              {t(bi("Power", "Potencia"))}
            </span>
            <span>
              <i className="ground" />
              {t(bi("Ground", "Tierra"))}
            </span>
            <span>
              <i className="signals" />
              {t(bi("Communication", "Comunicación"))}
            </span>
            <span className="dashed-key">
              {t(
                bi(
                  "Dashed = proposed / unverified",
                  "Discontinuo = propuesto / sin verificar",
                ),
              )}
            </span>
          </div>
        </div>
        <aside className="wiring-detail" aria-live="polite">
          <span className="eyebrow">
            {t(bi("COMPONENT PINOUT", "PINES DEL COMPONENTE"))}
          </span>
          <h3>
            {node?.label ??
              t(bi("Select a subsystem.", "Selecciona un subsistema."))}
          </h3>
          <p>
            {node
              ? t(node.detail)
              : t(
                  bi(
                    "Inspect the connections around a node, then search the table for a physical pin, BCM number, port or net. Layout is functional, not physical wire routing.",
                    "Inspecciona un nodo y busca en la tabla un pin físico, BCM, puerto o red. El diagrama es funcional, no el recorrido físico de cables.",
                  ),
                )}
          </p>
          {node && (
            <>
              <strong className="voltage-note">{t(node.voltage)}</strong>
              <div className="pin-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>{t(bi("Connector / pin", "Conector / pin"))}</th>
                      <th>{t(bi("Function / GPIO", "Función / GPIO"))}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {connectionRows
                      .filter(
                        (row) => row.from === selected || row.to === selected,
                      )
                      .map((row) => (
                        <tr key={row.id}>
                          <td>
                            {row.pin} → {row.destination}
                          </td>
                          <td>
                            {row.net} / {row.gpio}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
                {node.refs.length === 0 && (
                  <p>
                    {t(
                      bi(
                        "No verified contact-level pinout in this repository.",
                        "Sin contactos verificados en el repositorio.",
                      ),
                    )}
                  </p>
                )}
              </div>
            </>
          )}
          <a
            className="text-link"
            href={wiringEvidence}
            target="_blank"
            rel="noreferrer"
          >
            {t(bi("Wiring evidence", "Fuente del cableado"))}
            <ArrowUpRight size={14} />
          </a>
        </aside>
      </div>
      <div className="connection-table-heading">
        <h3>{t(bi("Trace every connection.", "Traza cada conexión."))}</h3>
        <label className="wire-search">
          <Search size={17} />
          <input
            type="search"
            aria-label={t(bi("Search connections", "Buscar conexiones"))}
            placeholder={t(
              bi("Pin, net, GPIO, voltage…", "Pin, red, GPIO, voltaje…"),
            )}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>
      <p className="caption">
        {rows.length}{" "}
        {t(
          bi(
            "connections shown. Pi numbers are physical header pins; BCM is separate. Display/audio follow the builder's confirmed table. TBD marks future pin assignments.",
            "conexiones. Los números Pi son pines físicos; BCM es independiente. Pantalla/audio siguen la tabla confirmada. TBD indica pines futuros pendientes.",
          ),
        )}
      </p>
      <a
        className="text-link"
        href="https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio"
        target="_blank"
        rel="noreferrer"
      >
        {t(
          bi(
            "BCM numbering & 3.3 V GPIO reference ?",
            "Referencia BCM y GPIO de 3.3 V ?",
          ),
        )}
      </a>
      <div className="connection-table-scroll">
        <table className="connection-table">
          <thead>
            <tr>
              <th>{t(bi("Source pin", "Pin origen"))}</th>
              <th>{t(bi("Destination", "Destino"))}</th>
              <th>BCM / GPIO</th>
              <th>{t(bi("Net / voltage", "Red / voltaje"))}</th>
              <th>{t(bi("Evidence", "Evidencia"))}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.pin}</td>
                <td>{row.destination}</td>
                <td>{row.gpio}</td>
                <td>
                  <strong>{row.net}</strong>
                  <small>{row.voltage}</small>
                </td>
                <td>
                  <span className={`connection-status ${row.status}`}>
                    {t(wiringStates[row.status])}
                  </span>
                  <a href={row.source} target="_blank" rel="noreferrer">
                    {t(bi("Source ↗", "Fuente ↗"))}
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="empty-connections">
            {t(
              bi(
                "No matching connections. Clear the search, filter or selected node.",
                "Sin coincidencias. Borra la búsqueda, filtro o nodo seleccionado.",
              ),
            )}
          </p>
        )}
      </div>
      <details className="engineering-conflicts" open>
        <summary>
          {t(
            bi(
              "Unresolved electrical checks & safety",
              "Revisiones eléctricas pendientes y seguridad",
            ),
          )}
        </summary>
        <ul>
          <li>
            {t(
              bi(
                "Preserve the working display/audio overlays. BCM10/11 belong to display SPI, BCM17 to touch IRQ, and BCM18 to I2S BCLK. Do not use the ReSpeaker RGB LEDs/button or share BCM18 with backlight.",
                "Conserva los overlays que funcionan. BCM10/11 son SPI de pantalla, BCM17 Touch IRQ y BCM18 I2S BCLK. No usar LED RGB/botón ReSpeaker ni BCM18 para retroiluminación.",
              ),
            )}
          </li>
          <li>
            {t(
              bi(
                "Backlight, final overlay, STM32 UART and all five PWM pin assignments remain pending. CAD pin suggestions are separate from the confirmed hookup list.",
                "Retroiluminación, overlay final, UART STM32 y los cinco pines PWM siguen pendientes. Las propuestas CAD se mantienen separadas del cableado confirmado.",
              ),
            )}
          </li>
          <li>
            {t(
              bi(
                "Measure about 6.0 V at the buck before connecting servos. Verify simultaneous current capacity. Share GND among Pi, STM32 and servo supply; never join positive outputs at different voltages.",
                "Mide unos 6.0 V en el buck antes de conectar servos. Verifica corriente simultánea. Comparte GND entre Pi, STM32 y fuente servo; nunca unas salidas positivas de distinto voltaje.",
              ),
            )}
          </li>
          <li>
            {t(
              bi(
                "LiPo protection, fuse/distribution, exact buck model/current, battery-to-Pi regulator and final PCB connectors need confirmation. Power the Pi through a compatible 5.1 V USB-C source, never raw LiPo or the 6 V servo rail.",
                "Protección LiPo, fusible/distribución, buck exacto/corriente, regulador batería–Pi y conectores finales PCB requieren confirmación. Alimenta la Pi por USB-C compatible de 5.1 V, nunca LiPo directa ni riel servo de 6 V.",
              ),
            )}
          </li>
        </ul>
        <a
          className="text-link"
          href={source(`${carrier.source}/README.md`)}
          target="_blank"
          rel="noreferrer"
        >
          {t(
            bi("Read the carrier design notes ↗", "Leer las notas de diseño ↗"),
          )}
        </a>
      </details>
    </section>
  );
}

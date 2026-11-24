/** Contrato de telemetría de solo lectura; el transporte no tiene API de movimiento. */
export interface RobotSnapshot {
  connection: "offline" | "connected";
  mode: "simulation" | "test" | "robot";
  safetyState: string;
  lastKnownState: string;
  motionAuthorized: boolean;
  controllerActive: boolean;
  physicalOutputStatus: "unverified";
  firmwareProfileMatch: "unverified";
  telemetryFresh: boolean;
  positionKind: "commanded";
  measuredPositionsAvailable: false;
  commandedMilliUnits: Record<string, number> | null;
  rxErrors: number | null;
  droppedTx: number | null;
  uartStatus: string | null;
}

export interface RobotTransport {
  getSnapshot(): RobotSnapshot;
  subscribe(listener: (snapshot: RobotSnapshot) => void): () => void;
}

const offlineSnapshot: RobotSnapshot = {
  connection: "offline",
  mode: "simulation",
  safetyState: "UNKNOWN",
  lastKnownState: "UNKNOWN",
  motionAuthorized: false,
  controllerActive: false,
  physicalOutputStatus: "unverified",
  firmwareProfileMatch: "unverified",
  telemetryFresh: false,
  positionKind: "commanded",
  measuredPositionsAvailable: false,
  commandedMilliUnits: null,
  rxErrors: null,
  droppedTx: null,
  uartStatus: null,
};

export const offlineRobot: RobotTransport = {
  getSnapshot: () => offlineSnapshot,
  subscribe: () => () => {},
};

function parseSnapshot(payload: unknown): RobotSnapshot | null {
  if (!payload || typeof payload !== "object") return null;
  const value = payload as Record<string, unknown>;
  const positions = value.commanded_milli_units;
  const commandedMilliUnits =
    positions && typeof positions === "object" &&
    ["HEAD_PAN", "LEFT_ARM", "RIGHT_ARM"].every(
      (axis) => Number.isInteger((positions as Record<string, unknown>)[axis]),
    )
      ? (positions as Record<string, number>)
      : null;
  if (
    !(value.connection === "offline" || value.connection === "connected") ||
    !(value.mode === "simulation" || value.mode === "test" || value.mode === "robot") ||
    typeof value.safety_state !== "string" ||
    typeof value.last_known_state !== "string" ||
    typeof value.motion_authorized !== "boolean" ||
    typeof value.controller_active !== "boolean" ||
    value.physical_output_status !== "unverified" ||
    value.firmware_profile_match !== "unverified" ||
    value.position_kind !== "commanded" ||
    value.measured_positions_available !== false ||
    typeof value.telemetry_fresh !== "boolean"
  ) return null;
  return {
    connection: value.connection,
    mode: value.mode,
    safetyState: value.safety_state,
    lastKnownState: value.last_known_state,
    motionAuthorized: value.motion_authorized,
    controllerActive: value.controller_active,
    physicalOutputStatus: "unverified",
    firmwareProfileMatch: "unverified",
    telemetryFresh: value.telemetry_fresh,
    positionKind: "commanded",
    measuredPositionsAvailable: false,
    commandedMilliUnits,
    rxErrors: typeof value.rx_errors === "number" ? value.rx_errors : null,
    droppedTx: typeof value.dropped_tx === "number" ? value.dropped_tx : null,
    uartStatus: typeof value.uart_status === "string" ? value.uart_status : null,
  };
}

/** Consulta periódicamente un endpoint configurado; nunca envía comandos. */
export class HttpRobotTransport implements RobotTransport {
  private snapshot = offlineSnapshot;
  private listeners = new Set<(snapshot: RobotSnapshot) => void>();
  private timer: number | undefined;
  private stopped = true;

  constructor(
    private readonly url: string,
    private readonly request: typeof fetch = fetch,
    private readonly intervalMs = 1000,
  ) {}

  getSnapshot(): RobotSnapshot {
    return this.snapshot;
  }

  subscribe(listener: (snapshot: RobotSnapshot) => void): () => void {
    this.listeners.add(listener);
    listener(this.snapshot);
    if (this.stopped) {
      this.stopped = false;
      void this.poll();
    }
    return () => {
      this.listeners.delete(listener);
      if (this.listeners.size === 0) {
        this.stopped = true;
        window.clearTimeout(this.timer);
      }
    };
  }

  private async poll(): Promise<void> {
    if (this.stopped) return;
    try {
      const response = await this.request(this.url, { cache: "no-store" });
      const next = response.ok ? parseSnapshot(await response.json()) : null;
      this.publish(next ?? offlineSnapshot);
    } catch {
      this.publish(offlineSnapshot);
    } finally {
      if (!this.stopped) {
        this.timer = window.setTimeout(() => void this.poll(), this.intervalMs);
      }
    }
  }

  private publish(snapshot: RobotSnapshot): void {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener(snapshot));
  }
}

const statusUrl = import.meta.env.VITE_ROBOT_STATUS_URL?.trim();
export const robotTransport: RobotTransport = statusUrl
  ? new HttpRobotTransport(statusUrl, fetch, 100)
  : offlineRobot;

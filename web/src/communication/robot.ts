/** Future boundary. No network connection, telemetry or hardware commands in v1. */
export interface RobotSnapshot {
  connection: "offline" | "connected";
  expression: string | null;
  batteryVolts: number | null;
}
export interface RobotTransport {
  getSnapshot(): RobotSnapshot;
  subscribe(listener: (snapshot: RobotSnapshot) => void): () => void;
}
export const offlineRobot: RobotTransport = {
  getSnapshot: () => ({
    connection: "offline",
    expression: null,
    batteryVolts: null,
  }),
  subscribe: () => () => {},
};

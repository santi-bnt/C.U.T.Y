import { afterEach, describe, expect, it, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import { HttpRobotTransport } from "./robot";

afterEach(() => vi.restoreAllMocks());

describe("read-only robot telemetry", () => {
  it("maps commanded positions and does not claim physical measurements", async () => {
    const request = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({
      connection: "connected",
      mode: "hardware",
      safety_state: "DISARMED",
      motion_authorized: true,
      controller_active: false,
      physical_output_status: "unverified",
      firmware_profile_match: "unverified",
      telemetry_fresh: true,
      position_kind: "commanded",
      measured_positions_available: false,
      commanded_milli_units: { HEAD_PAN: -100, LEFT_ARM: 200, RIGHT_ARM: 0 },
      rx_errors: 0,
      dropped_tx: 0,
      uart_status: "OK",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const transport = new HttpRobotTransport("http://127.0.0.1:8765/api/robot/status", request);
    const unsubscribe = transport.subscribe(() => {});
    await waitFor(() => expect(transport.getSnapshot().connection).toBe("connected"));
    expect(transport.getSnapshot()).toMatchObject({
      safetyState: "DISARMED",
      positionKind: "commanded",
      measuredPositionsAvailable: false,
      commandedMilliUnits: { HEAD_PAN: -100, LEFT_ARM: 200, RIGHT_ARM: 0 },
    });
    expect(request).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/api/robot/status", { cache: "no-store" },
    );
    unsubscribe();
  });

  it("shows offline state when the endpoint is unavailable", async () => {
    const request = vi.fn<typeof fetch>().mockRejectedValue(new Error("offline"));
    const transport = new HttpRobotTransport("http://127.0.0.1:8765/api/robot/status", request);
    const unsubscribe = transport.subscribe(() => {});
    await waitFor(() => expect(transport.getSnapshot().connection).toBe("offline"));
    expect(transport.getSnapshot().mode).toBe("simulation");
    unsubscribe();
  });
});

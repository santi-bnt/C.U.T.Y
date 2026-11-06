import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { BoxGeometry, Mesh } from "three";
import App from "./App";
import { LocaleProvider } from "./state/Locale";
import { measureModel } from "./viewer/model";
import { offlineRobot } from "./communication/robot";
vi.mock("./viewer/RobotViewer", () => ({
  default: () => <div>3D test boundary</div>,
}));
vi.mock("./components/Choreography", () => ({ default: () => null }));
afterEach(cleanup);
describe("portfolio interactions", () => {
  it("starts in English, switches content and document language to Spanish", async () => {
    render(
      <LocaleProvider>
        <App />
      </LocaleProvider>,
    );
    expect(screen.getByText("A curious mind.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Español" }));
    expect(screen.getByText("Una mente curiosa.")).toBeTruthy();
    await waitFor(() => expect(document.documentElement.lang).toBe("es"));
    expect(
      screen
        .getByRole("link", { name: /Arquitectura técnica/ })
        .getAttribute("href"),
    ).toBe("#architecture");
  });
  it("exposes truthful contextual component and future controller details", () => {
    render(
      <LocaleProvider>
        <App />
      </LocaleProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Carrier PCB/ }));
    expect(
      screen.getByText(/100 × 92 mm, two-layer KiCad carrier/),
    ).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: /FUTURE REAL-TIME CONTROL/ }),
    );
    expect(
      screen.getByText(/Current firmware files are placeholders/),
    ).toBeTruthy();
  });
  it("changes face illustration and toggles synthetic mouth motion", () => {
    render(
      <LocaleProvider>
        <App />
      </LocaleProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Happy" }));
    expect(document.querySelector(".face-screen.happy")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Animate mouth" }));
    expect(document.querySelector(".face-screen.talking")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Stop mouth" }));
    expect(document.querySelector(".face-screen.talking")).toBeNull();
  });
  it("opens the compact navigation and closes it when a destination is selected", () => {
    render(
      <LocaleProvider>
        <App />
      </LocaleProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Toggle navigation" }));
    expect(document.querySelector(".nav.open")).toBeTruthy();
    fireEvent.click(screen.getByRole("link", { name: "Development" }));
    expect(document.querySelector(".nav.open")).toBeNull();
  });
});
describe("3D normalization and communication boundary", () => {
  it("fits translated geometry without changing its axis proportions", () => {
    const mesh = new Mesh(new BoxGeometry(2, 4, 1));
    mesh.position.set(8, 12, -5);
    const { size, center, scale } = measureModel(mesh);
    expect(size.toArray()).toEqual([2, 4, 1]);
    expect(center.toArray()).toEqual([8, 12, -5]);
    expect(scale).toBe(0.75);
  });
  it("does not invent telemetry while offline", () => {
    expect(offlineRobot.getSnapshot()).toEqual({
      connection: "offline",
      expression: null,
      batteryVolts: null,
    });
  });
});

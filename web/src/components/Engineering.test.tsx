import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { LocaleProvider } from "../state/Locale";
import PcbDesign from "./PcbDesign";
import WiringConnections from "./WiringConnections";
vi.mock("./EngineeringViewport", () => ({
  default: () => <div>3D boundary</div>,
}));
afterEach(cleanup);
describe("source-backed engineering interfaces", () => {
  it("selects a native footprint, exposes pin nets, flips actual previews and labels the missing 3D asset", () => {
    render(
      <LocaleProvider>
        <PcbDesign />
      </LocaleProvider>,
    );
    fireEvent.change(screen.getByLabelText("Select component"), {
      target: { value: "U1" },
    });
    expect(screen.getByText("BlackPill F401CC")).toBeTruthy();
    expect(screen.getByText("29 / PA3")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /^Back$/ }));
    expect(
      document.querySelector(".pcb-canvas image")?.getAttribute("href"),
    ).toContain("carrier-back.png");
    fireEvent.click(
      screen.getByRole("button", { name: "3D mechanical reference" }),
    );
    expect(
      screen.getByText(/Recovered from the revised Nido CAD/),
    ).toBeTruthy();
    expect(
      screen
        .getByRole("link", { name: "Gerbers + drills" })
        .getAttribute("href"),
    ).toContain("carrier-gerbers.zip");
  });
  it("searches real connection rows and shows the selected subsystem's unresolved power requirements", () => {
    render(
      <LocaleProvider>
        <WiringConnections />
      </LocaleProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: /^UART$/ }));
    expect(
      document.querySelectorAll(".connection-table tbody tr"),
    ).toHaveLength(2);
    fireEvent.change(screen.getByLabelText("Search connections"), {
      target: { value: "BCM 14" },
    });
    expect(
      document.querySelectorAll(".connection-table tbody tr"),
    ).toHaveLength(1);
    expect(
      document.querySelector(".connection-table tbody")?.textContent,
    ).toContain("STM32 RX");
    fireEvent.click(
      screen.getByRole("button", {
        name: "Adjustable servo buck",
      }),
    );
    expect(document.querySelector(".wiring-detail")?.textContent).toContain(
      "current remain unverified",
    );
    expect(
      document.querySelectorAll(".connection-table tbody tr"),
    ).toHaveLength(0);
    expect(screen.getByText(/No matching connections/)).toBeTruthy();
  });
});

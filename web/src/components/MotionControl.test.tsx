import { afterEach, describe, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { LocaleProvider, useLocale } from "../state/Locale";
import MotionControl from "./MotionControl";
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});
function Language() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("es")}>ES</button>;
}
function mount() {
  return render(
    <LocaleProvider>
      <Language />
      <MotionControl />
    </LocaleProvider>,
  );
}
describe("local motion education", () => {
  it("steps through a local example and latches the illustrative heartbeat fault until demo reset", () => {
    mount();
    for (let i = 0; i < 7; i++)
      fireEvent.click(screen.getByRole("button", { name: "Next step" }));
    expect(screen.getByRole("status").textContent).toContain("7/8");
    fireEvent.click(
      screen.getByRole("button", { name: "Simulate heartbeat loss" }),
    );
    expect(screen.getByRole("status").textContent).toContain("ACTIVE → FAULT");
    expect(
      (screen.getByRole("button", { name: "Next step" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Reset demo" }));
    expect(screen.getByRole("status").textContent).toContain(
      "No data is transmitted",
    );
  });
  it("translates the explanation and exposes truthful source/status details", () => {
    mount();
    fireEvent.click(screen.getByText("ES"));
    expect(screen.getByRole("button", { name: "Siguiente paso" })).toBeTruthy();
    expect(
      screen.getByText(
        /integración FreeRTOS, UART y PWM en placa sigue pendiente/,
      ),
    ).toBeTruthy();
    expect(screen.getByText(/Implemented: parser portable/)).toBeTruthy();
    expect(document.querySelectorAll(".motion-task")).toHaveLength(5);
  });
  it("autoplays and cancels stage changes when paused", () => {
    vi.useFakeTimers();
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Play simulation" }));
    act(() => vi.advanceTimersByTime(1800));
    expect(screen.getByRole("status").textContent).toContain("1/8");
    fireEvent.click(screen.getByRole("button", { name: "Pause simulation" }));
    const status = screen.getByRole("status").textContent;
    vi.advanceTimersByTime(10000);
    expect(screen.getByRole("status").textContent).toBe(status);
  });
  it("offers manual stages instead of autoplay with reduced motion", () => {
    const original = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    try {
      mount();
      expect(
        screen.queryByRole("button", { name: "Play simulation" }),
      ).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Next step" }));
      expect(screen.getByRole("status").textContent).toContain("1/8");
    } finally {
      window.matchMedia = original;
    }
  });
});

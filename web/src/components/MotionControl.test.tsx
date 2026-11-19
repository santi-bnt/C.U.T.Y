import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { LocaleProvider, useLocale } from "../state/Locale";
import MotionControl from "./MotionControl";

afterEach(() => { cleanup(); vi.useRealTimers(); });

function Language() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("es")}>ES</button>;
}

function mount() {
  return render(<LocaleProvider><Language /><MotionControl /></LocaleProvider>);
}

describe("FreeRTOS motion section", () => {
  it("presents the connected architecture and task inspector", () => {
    mount();
    expect(screen.getByText(/How C.U.T.Y. translates perception/)).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Raspberry Pi 5" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: /STM32F401 \+ FreeRTOS/ })).toBeTruthy();
    expect(document.querySelector(".mc-reserved-note")?.textContent).toContain("J10 / J11 reserved");
    const comm = document.querySelector('.mc-task-node[data-node="communication"]') as HTMLButtonElement;
    expect(comm).toBeTruthy();
    fireEvent.click(comm);
    expect(comm.getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelector('[data-node="communication"]')?.getAttribute("data-selected")).toBe("true");
    expect(screen.getByLabelText("Selected task details").textContent).toContain("portable parser");
    expect(document.querySelectorAll(".mc-task-node")).toHaveLength(4);
    fireEvent.click(screen.getByText("Future extensions"));
    expect(screen.getByText(/IMUTask.*not implemented/)).toBeTruthy();
  });

  it("drives the diagram from the eight-stage simulation and heartbeat fault", () => {
    mount();
    expect(screen.getByRole("status").textContent).toContain("Step 1 of 8");
    for (let i = 0; i < 2; i++) fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByRole("status").textContent).toContain("Step 3 of 8");
    expect(document.querySelector('[data-node="communication"]')?.getAttribute("data-active")).toBe("true");
    expect(document.querySelector('[data-wire="uart-to-comm"]')?.getAttribute("data-active")).toBe("true");
    for (let i = 0; i < 5; i++) fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(document.querySelector('[data-node="safety"]')?.getAttribute("data-active")).toBe("true");
    expect(document.querySelector('.mc-fault-branch strong[data-current="true"]')?.textContent).toBe("FAULT");
    fireEvent.click(screen.getByRole("button", { name: "Simulate heartbeat loss" }));
    expect(screen.getByRole("status").textContent).toContain("ACTIVE");
    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(screen.getByRole("status").textContent).toContain("Step 1 of 8");
  });

  it("autoplays, pauses and supports Spanish copy", () => {
    vi.useFakeTimers();
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    act(() => vi.advanceTimersByTime(1800));
    expect(screen.getByRole("status").textContent).toContain("Step 2 of 8");
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    const state = screen.getByRole("status").textContent;
    act(() => vi.advanceTimersByTime(5000));
    expect(screen.getByRole("status").textContent).toBe(state);
    fireEvent.click(screen.getByText("ES"));
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Salidas a actuadores" })).toBeTruthy();
  });
});

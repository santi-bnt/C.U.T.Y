import { afterEach, describe, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
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

describe("FreeRTOS motion section", () => {
  it("shows a selectable architecture and four task cards with advanced details", () => {
    mount();
    expect(screen.getByText(/How C.U.T.Y. translates perception/)).toBeTruthy();
    expect(screen.getByText(/CMSIS-RTOS2/)).toBeTruthy();
    const stm = screen.getByRole("button", { name: /STM32F401 \+ FreeRTOS/ });
    fireEvent.click(stm);
    expect(stm.getAttribute("aria-pressed")).toBe("true");

    const taskCards = within(
      screen.getByRole("group", { name: "FreeRTOS tasks" }),
    );
    const communication = taskCards.getByRole("button", {
      name: /CommunicationTask/,
    });
    fireEvent.click(communication);
    expect(communication.getAttribute("aria-pressed")).toBe("true");
    expect(
      screen.getByLabelText("Selected task details").textContent,
    ).toContain("Implemented: portable parser");
    expect(document.querySelectorAll(".mc-task-card")).toHaveLength(4);

    fireEvent.click(screen.getByText("Future extensions"));
    expect(screen.getByText(/IMUTask · not implemented/)).toBeTruthy();
  });

  it("steps through the eight-stage flow and latches the illustrative heartbeat fault", () => {
    mount();
    expect(screen.getByRole("status").textContent).toContain("Step 1 of 8");
    for (let i = 0; i < 7; i++)
      fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(document.querySelector(".mc-sim-progress")?.textContent).toContain(
      "Step 8 of 8",
    );
    expect(
      document.querySelector('.mc-task-card[data-flow-active="true"]')
        ?.textContent,
    ).toContain("SafetyTask");
    expect(
      document.querySelector('.mc-fault-branch strong[data-current="true"]')
        ?.textContent,
    ).toBe("FAULT");
    fireEvent.click(
      screen.getByRole("button", { name: "Simulate heartbeat loss" }),
    );
    expect(screen.getByRole("status").textContent).toContain("ACTIVE → FAULT");
    expect(
      (screen.getByRole("button", { name: "Next" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(document.querySelector(".mc-sim-progress")?.textContent).toContain(
      "Step 1 of 8",
    );
    expect(screen.getByRole("status").textContent).toContain(
      "no data is transmitted",
    );
  });

  it("autoplays and pauses without advancing after pause", () => {
    vi.useFakeTimers();
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    act(() => vi.advanceTimersByTime(1800));
    expect(screen.getByRole("status").textContent).toContain("Step 2 of 8");
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    const status = screen.getByRole("status").textContent;
    act(() => vi.advanceTimersByTime(10000));
    expect(screen.getByRole("status").textContent).toBe(status);
  });

  it("keeps manual controls available, translates copy, and respects reduced motion", () => {
    const original = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    try {
      mount();
      expect(screen.queryByRole("button", { name: "Play" })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Next" }));
      expect(screen.getByRole("status").textContent).toContain("Step 2 of 8");
      fireEvent.click(screen.getByText("ES"));
      expect(screen.getByRole("button", { name: "Siguiente" })).toBeTruthy();
      expect(
        screen.getByText(/Ruta de software integrada — falta validar calibración/),
      ).toBeTruthy();
      const communication = within(
        screen.getByRole("group", { name: "Tareas FreeRTOS" }),
      ).getByRole("button", { name: /CommunicationTask/ });
      fireEvent.click(communication);
      expect(communication.getAttribute("aria-pressed")).toBe("true");
    } finally {
      window.matchMedia = original;
    }
  });
});

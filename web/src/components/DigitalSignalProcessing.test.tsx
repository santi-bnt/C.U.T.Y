import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { LocaleProvider, useLocale } from "../state/Locale";
import DigitalSignalProcessing from "./DigitalSignalProcessing";

afterEach(cleanup);

function Language() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("es")}>ES</button>;
}

function mount() {
  return render(<LocaleProvider><Language /><DigitalSignalProcessing /></LocaleProvider>);
}

describe("digital signal processing education", () => {
  it("calculates and displays the two filters and interactive synthetic plots", () => {
    mount();
    expect(screen.getByText(/0.2, 0.2, 0.2, 0.2, 0.2/)).toBeTruthy();
    expect(screen.getAllByRole("img")).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: /band-pass/ }));
    expect(screen.getByText(/511 symmetric Hamming-windowed taps/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Filtered" }));
    const slider = screen.getByRole("slider") as HTMLInputElement;
    fireEvent.change(slider, { target: { value: "3000" } });
    expect(slider.value).toBe("3000");
  });

  it("translates the technical explanation", () => {
    mount();
    fireEvent.click(screen.getByText("ES"));
    fireEvent.click(screen.getByRole("button", { name: /Voz · pasa-banda/ }));
    expect(screen.getByText(/Se eligieron 511 taps/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Voz · pasa-banda/ })).toBeTruthy();
  });
});

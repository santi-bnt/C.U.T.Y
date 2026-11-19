import { expect, test } from "@playwright/test";

test("DSP section switches real FIR calculations and fits the viewport", async ({ page }) => {
  await page.goto("/#dsp-filters", { waitUntil: "domcontentloaded" });
  const section = page.locator("#dsp-filters");
  await section.waitFor({ state: "attached", timeout: 15_000 });
  const nextSection = await section.evaluate((node) => node.nextElementSibling?.id);
  expect(nextSection).toBe("about");
  await expect(section).toHaveCSS("background-color", "rgb(23, 23, 23)");
  await expect(section.getByRole("heading", { name: "Digital Signal Processing / FIR Filters" })).toBeVisible();
  await expect(section.getByRole("button", { name: "Head tracking · low-pass" })).toHaveAttribute("aria-pressed", "true");
  await section.getByRole("button", { name: "Speech · band-pass" }).click();
  await expect(section.getByRole("button", { name: "Speech · band-pass" })).toHaveAttribute("aria-pressed", "true");
  await expect(section.getByRole("button", { name: "Head tracking · low-pass" })).toHaveAttribute("aria-pressed", "false");
  await expect(section.getByText(/511 symmetric Hamming-windowed taps/)).toBeVisible();
  await section.getByRole("button", { name: "Filtered" }).click();
  await expect(section.getByRole("button", { name: "Filtered" })).toHaveAttribute("aria-pressed", "true");
  await expect(section.locator(".dsp-original")).toHaveCount(0);
  await expect(section.locator("svg[role=img]")).toHaveCount(3);
  const fits = await section.evaluate((node) => node.scrollWidth <= node.clientWidth + 1);
  expect(fits).toBe(true);
});

import { expect, test } from "@playwright/test";

test("DSP section switches real FIR calculations and fits the viewport", async ({ page }) => {
  await page.goto("/#dsp-filters", { waitUntil: "domcontentloaded" });
  const section = page.locator("#dsp-filters");
  await section.waitFor({ state: "attached", timeout: 15_000 });
  await expect(section).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(section.getByRole("heading", { name: "Digital Signal Processing / FIR Filters" })).toBeVisible();
  await section.getByRole("button", { name: "Speech · band-pass" }).click();
  await expect(section.getByText(/511 symmetric Hamming-windowed taps/)).toBeVisible();
  await section.getByRole("button", { name: "Filtered" }).click();
  await expect(section.locator("svg[role=img]")).toHaveCount(3);
  const fits = await section.evaluate((node) => node.scrollWidth <= node.clientWidth + 1);
  expect(fits).toBe(true);
});

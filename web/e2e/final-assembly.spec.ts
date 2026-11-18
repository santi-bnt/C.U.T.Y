import { expect, test } from "@playwright/test";
test("final assembly stages match their descriptions and respect reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#assembly");
  const section = page.locator("#assembly");
  const strip = section.locator(".assembly-strip");
  for (const [index, title, image] of [
    [15, "Small gestures", "fixed-16-still.webp"],
    [16, "A removable home", "fixed-17-still.webp"],
    [17, "Taking shape", "fixed-18.webp"],
  ] as const) {
    await strip.locator("button").nth(index).click();
    await expect(section.locator(".assembly-caption h3")).toHaveText(title);
    await expect.poll(() => section.locator(".assembly-image img").evaluate((element) => (element as HTMLImageElement).currentSrc)).toContain(image);
  }
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await strip.locator("button").nth(15).click();
  await expect.poll(() => section.locator(".assembly-image img").evaluate((element) => (element as HTMLImageElement).currentSrc)).toContain("fixed-16.webp");
  await strip.locator("button").nth(16).click();
  await expect.poll(() => section.locator(".assembly-image img").evaluate((element) => (element as HTMLImageElement).currentSrc)).toContain("fixed-17.webp");
});

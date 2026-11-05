import { expect, test } from "@playwright/test";
test("real model, camera controls, translation, panels and responsive layout", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.goto("/");
  await expect(page.locator("canvas")).toBeVisible();
  await expect(page.getByText("Loading real GLB…")).toBeHidden({
    timeout: 30_000,
  });
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByText("REAL ASSEMBLY / V16")).toBeVisible();
  for (const name of ["Front", "Side", "Top", "Isometric"]) {
    await page.getByRole("button", { name, exact: true }).click();
    await expect(
      page.getByRole("button", { name, exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
  }
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await page.getByRole("button", { name: "Zoom out", exact: true }).click();
  await page.getByRole("button", { name: "Wireframe", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Wireframe", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Wireframe", exact: true }).click();
  await page.getByRole("button", { name: "Auto-rotate", exact: true }).click();
  await page.getByRole("button", { name: "Auto-rotate", exact: true }).click();
  await page.getByRole("button", { name: "Reset camera", exact: true }).click();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.screenshot({ path: `test-results/${info.project.name}-hero.png` });
  await page.getByRole("button", { name: /Carrier PCB/ }).click();
  await expect(
    page.getByText(/100 × 92 mm, two-layer KiCad carrier/),
  ).toBeVisible();
  await page.getByRole("button", { name: /FUTURE REAL-TIME CONTROL/ }).click();
  await expect(
    page.getByText(/Current firmware files are placeholders/),
  ).toBeVisible();
  await page.getByRole("button", { name: "Happy", exact: true }).click();
  await page
    .getByRole("button", { name: "Animate mouth", exact: true })
    .click();
  await expect(page.locator(".face-screen")).toHaveClass(/talking/);
  const face = page.locator(".face-original img");
  await expect(face).toHaveAttribute("src", /face\/happy\.webp$/);
  await expect
    .poll(() => face.evaluate((image: HTMLImageElement) => image.naturalWidth))
    .toBe(2400);
  await page
    .locator(".face-demo")
    .screenshot({ path: `test-results/${info.project.name}-face.png` });
  await page.getByRole("button", { name: "Español", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(page.getByText("Una mente curiosa.")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  const missingAnchors = await page
    .locator('a[href^="#"]')
    .evaluateAll((links) =>
      links
        .map((a) => a.getAttribute("href")!)
        .filter((href) => href.length > 1 && !document.querySelector(href)),
    );
  expect(missingAnchors).toEqual([]);
  await expect(page.locator("h1")).toHaveCount(1);
  await page.screenshot({
    path: `test-results/${info.project.name}-full.png`,
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
test("reduced motion and a missing GLB produce usable UI", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Auto-rotate", exact: true }),
  ).toBeDisabled();
  await page.route("**/models/cuty.glb*", (route) =>
    route.fulfill({ status: 404, body: "Model missing" }),
  );
  await page.reload();
  await expect(page.getByRole("alert")).toContainText(
    "web/public/models/cuty.glb",
    { timeout: 30_000 },
  );
  await expect(
    page.getByRole("link", { name: "Technical Architecture", exact: true }),
  ).toBeVisible();
});

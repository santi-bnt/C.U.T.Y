import { expect, test } from "@playwright/test";

test("Wiring evidence opens and returns in the same tab with responsive navigation", async ({ page }, info) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto("/#wiring");
  const skip = page.getByRole("button", { name: "Skip intro", exact: true });
  if (await skip.isVisible()) await skip.click();

  const wiring = page.locator("#wiring");
  const evidenceLink = wiring.getByRole("link", { name: /Wiring evidence/ });
  await expect(evidenceLink).not.toHaveAttribute("target", "_blank");
  await evidenceLink.click();
  await expect(page).toHaveURL(/\/engineering\/wiring-evidence\.html(?:\?.*)?$/);
  await expect(page.getByRole("heading", { name: "Connections, by block." })).toBeVisible();
  await expect(page.locator("html")).toHaveCSS("scroll-behavior", "smooth");
  expect(page.context().pages()).toHaveLength(1);
  const blockStyles = await page.locator(".flow-list .block").evaluateAll((blocks) =>
    blocks.map((block) => ({
      background: getComputedStyle(block).backgroundColor,
      border: getComputedStyle(block).borderTopColor,
      text: getComputedStyle(block).color,
      secondary: getComputedStyle(block.querySelector("small")!).color,
    })),
  );
  expect(new Set(blockStyles.map((block) => block.background))).toEqual(
    new Set(["rgb(248, 245, 242)"]),
  );
  expect(new Set(blockStyles.map((block) => block.border))).toEqual(
    new Set(["rgb(231, 226, 220)"]),
  );
  expect(new Set(blockStyles.map((block) => block.text))).toEqual(
    new Set(["rgb(23, 23, 23)"]),
  );
  expect(new Set(blockStyles.map((block) => block.secondary))).toEqual(
    new Set(["rgb(102, 102, 102)"]),
  );

  if (info.project.name !== "desktop") {
    await page.setViewportSize({ width: 390, height: 844 });
    const toggle = page.getByRole("button", { name: "Toggle navigation" });
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Wiring" })).toBeVisible();
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(page).toHaveURL(/wiring-evidence\.html/);
  }

  await page.getByRole("button", { name: "ES", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(page.getByRole("heading", { name: "Conexiones por bloques." })).toBeVisible();
  expect(await page.locator("body").evaluate((node) => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
  await page.screenshot({ path: `test-results/${info.project.name}-wiring-evidence.png`, fullPage: true });

  const returnLink = page.locator('.source-row a[href="../index.html#wiring"]');
  await returnLink.scrollIntoViewIfNeeded();
  await returnLink.click();
  await expect(page).toHaveURL(/index\.html#wiring$/);
  await expect(page.locator("#wiring").getByRole("heading", { name: "The connections matter." })).toBeVisible();
  expect(page.context().pages()).toHaveLength(1);
  expect(pageErrors).toEqual([]);
});

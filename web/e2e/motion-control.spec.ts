import { expect, test } from "@playwright/test";
test("motion section is local, bilingual, accessible and responsive", async ({
  page,
}, info) => {
  const connections: string[] = [];
  page.on("websocket", (socket) => connections.push(socket.url()));
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#motion-control");
  const skip = page.getByRole("button", { name: "Skip intro", exact: true });
  if (await skip.isVisible()) await skip.click();
  const section = page.locator("#motion-control");
  await section.scrollIntoViewIfNeeded();
  await expect(section).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(page.locator(".scene-layer")).toHaveAttribute(
    "data-chapter",
    "8",
  );
  await expect(page.locator(".scene-layer")).toHaveCSS("opacity", "0");
  await expect(
    section.getByRole("heading", {
      name: "FreeRTOS / Motion Control",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    section.getByRole("button", { name: "Play simulation" }),
  ).toHaveCount(0);
  await section
    .locator("summary")
    .filter({ hasText: "CommunicationTask" })
    .click();
  await expect(section.getByText(/Implemented: portable parser/)).toBeVisible();
  await section.getByRole("button", { name: "Next step", exact: true }).click();
  await expect(section.getByRole("status")).toContainText("1/8");
  await section
    .getByRole("button", { name: "Simulate heartbeat loss" })
    .click();
  await expect(section.getByRole("status")).toContainText("ACTIVE → FAULT");
  await section.getByRole("button", { name: "Reset demo" }).click();
  await expect(section.getByRole("status")).toContainText(
    "No data is transmitted",
  );
  await page.getByRole("button", { name: "Español", exact: true }).click();
  await expect(
    section.getByRole("button", { name: "Siguiente paso" }),
  ).toBeVisible();
  await expect(section).toContainText("sin conexión al robot");
  const overflow = await section.evaluate(
    (element) => element.scrollWidth > element.clientWidth,
  );
  expect(overflow).toBe(false);
  const nav = page.getByRole("navigation", { name: "Navegación principal" });
  if (info.project.name !== "desktop")
    await page.getByRole("button", { name: "Abrir navegación" }).click();
  await nav.getByRole("link", { name: "FreeRTOS", exact: true }).click();
  await expect(page).toHaveURL(/#motion-control$/);
  await expect(page.locator('nav a[href="#motion-control"]')).toHaveAttribute("aria-current", "location");
  const links = await page
    .locator(".site-header a:visible")
    .evaluateAll((elements) =>
      elements.map((e) => {
        const r = e.getBoundingClientRect();
        return { left: r.left, right: r.right, width: window.innerWidth };
      }),
    );
  expect(links.every((r) => r.left >= 0 && r.right <= r.width)).toBe(true);
  expect(
    connections.filter((url) => new URL(url).hostname !== "127.0.0.1"),
  ).toEqual([]);
  await section.screenshot({
    path: `test-results/${info.project.name}-motion-control.png`,
  });
});

import { expect, test } from "@playwright/test";

test("interactive embedded architecture works on desktop and mobile", async ({ page }, info) => {
  const connections: string[] = [];
  const originalViewport = page.viewportSize();
  page.on("websocket", (socket) => connections.push(socket.url()));
  await page.goto("/#motion-control");
  const skip = page.getByRole("button", { name: "Skip intro", exact: true });
  if (await skip.isVisible()) await skip.click();

  const section = page.locator("#motion-control");
  await section.scrollIntoViewIfNeeded();
  await expect(section).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(section.getByRole("heading", { name: "FreeRTOS / Motion Control" })).toBeVisible();
  await expect(section.getByRole("heading", { name: "Raspberry Pi 5" })).toBeVisible();
  await expect(section.getByRole("heading", { name: /STM32F401 \+ FreeRTOS/ })).toBeVisible();
  await expect(section.locator(".mc-architecture-grid")).toBeVisible();
  await expect(section.locator(".mc-task-node")).toHaveCount(4);
  await expect(section.locator(".mc-actuator-output")).toHaveCount(3);
  await expect(section.locator(".mc-reserved-note")).toContainText("J10 / J11 reserved");
  await expect(section.locator(".mc-pwm-note")).toContainText("not hardware-validated");

  const communication = section.locator('.mc-task-node[data-node="communication"]');
  await communication.click();
  await expect(communication).toHaveAttribute("aria-pressed", "true");
  await expect(section.locator(".mc-task-details")).toContainText("Implemented: portable parser");
  await expect(section.locator('[data-wire="uart-to-comm"]')).toHaveAttribute("data-related", "true");
  await section.locator('.mc-task-node[data-node="safety"]').click();
  await expect(section.locator(".mc-task-details")).toContainText("RESET");

  const controls = section.getByRole("group", { name: "Simulation controls" });
  await controls.getByRole("button", { name: "Reset" }).click();
  await controls.getByRole("button", { name: "Next" }).click();
  await controls.getByRole("button", { name: "Next" }).click();
  await expect(section.getByRole("status")).toContainText("Step 3 of 8");
  await expect(section.locator('[data-node="communication"]')).toHaveAttribute("data-active", "true");
  await expect(section.locator('[data-wire="uart-to-comm"]')).toHaveAttribute("data-active", "true");
  await controls.getByRole("button", { name: "Next" }).click();
  await expect(section.locator('[data-node="queues"]')).toHaveAttribute("data-active", "true");
  await controls.getByRole("button", { name: "Previous" }).click();
  await expect(section.getByRole("status")).toContainText("Step 3 of 8");

  await section.getByRole("button", { name: "Simulate heartbeat loss" }).click();
  await expect(section.getByRole("status")).toContainText(`ACTIVE \u2192 FAULT`);
  await expect(section.locator(".mc-fault-branch strong")).toHaveAttribute("data-current", "true");
  await expect(section.locator('[data-node="safety"]')).toHaveAttribute("data-active", "true");
  await section.getByRole("button", { name: "Reset" }).click();
  await expect(section.getByRole("status")).toContainText("Step 1 of 8");
  await section.locator(".mc-future summary").click();
  await expect(section.locator(".mc-future-content")).toContainText("IMUTask");
  await section.locator(".mc-sequence summary").click();
  await expect(section.locator(".mc-sequence li")).toHaveCount(8);
  await expect(section.getByRole("heading", { name: "Explicit arming. Latched fault." })).toBeVisible();

  await page.getByRole("button", { name: `Espa\u00f1ol`, exact: true }).click();
  await expect(section.getByRole("button", { name: "Siguiente" })).toBeVisible();
  await expect(section.getByRole("button", { name: `Simular p\u00e9rdida de heartbeat` })).toBeVisible();
  await expect(section).toContainText(`La Raspberry Pi procesa visi\u00f3n e IA`);
  expect(await section.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);

  await page.setViewportSize({ width: 320, height: 800 });
  expect(await section.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  await expect(section.locator(".mc-architecture-grid")).toBeVisible();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(section.getByRole("button", { name: "Play" })).toHaveCount(0);
  await expect(section.locator(".mc-reduced-note")).toBeVisible();

  await expect(page.locator('.site-header a[href="#motion-control"]')).toHaveCount(1);
  expect(connections.filter((url) => new URL(url).hostname !== "127.0.0.1")).toEqual([]);
  if (originalViewport) await page.setViewportSize(originalViewport);
  await section.screenshot({ path: `test-results/${info.project.name}-motion-control.png` });
});

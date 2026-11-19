import { expect, test } from "@playwright/test";

test("motion section explains architecture, tasks and safe local simulation", async ({
  page,
}, info) => {
  const connections: string[] = [];
  page.on("websocket", (socket) => connections.push(socket.url()));
  await page.goto("/#motion-control");
  const skip = page.getByRole("button", { name: "Skip intro", exact: true });
  if (await skip.isVisible()) await skip.click();

  const section = page.locator("#motion-control");
  await section.scrollIntoViewIfNeeded();
  await expect(section).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(
    section.getByRole("heading", { name: "FreeRTOS / Motion Control" }),
  ).toBeVisible();
  await expect(
    section.getByText(
      "How C.U.T.Y. translates perception into controlled movement.",
    ),
  ).toBeVisible();
  await expect(
    section.getByText("In development — Hardware integration pending"),
  ).toBeVisible();
  await expect(section.locator(".mc-status-strip")).toContainText(
    "preliminary dry-run",
  );

  const diagram = section.locator(".mc-diagram");
  const pi = diagram.getByRole("button", { name: /Raspberry Pi 5/ });
  const stm = diagram.getByRole("button", { name: /STM32F401 \+ FreeRTOS/ });
  const servos = diagram.getByRole("button", { name: /3 × MG996R/ });
  await expect(pi).toHaveAttribute("aria-pressed", "false");
  await stm.click();
  await expect(stm).toHaveAttribute("aria-pressed", "true");
  await servos.click();
  await expect(servos).toHaveAttribute("aria-pressed", "true");
  await pi.focus();
  await page.keyboard.press("Enter");
  await expect(pi).toHaveAttribute("aria-pressed", "true");

  const tasks = section.locator(".mc-task-grid");
  await expect(tasks.locator(".mc-task-card")).toHaveCount(4);
  const communication = tasks.getByRole("button", {
    name: /CommunicationTask/,
  });
  await communication.click();
  await expect(communication).toHaveAttribute("aria-pressed", "true");
  await expect(section.locator(".mc-task-details")).toContainText(
    "Implemented: portable parser",
  );
  await expect(section.locator(".mc-task-details")).toContainText("RX bytes");
  await tasks.getByRole("button", { name: /SafetyTask/ }).click();
  await expect(section.locator(".mc-task-details")).toContainText("RESET");
  await tasks.getByRole("button", { name: /CommunicationTask/ }).click();

  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Next" })
    .click();
  await expect(section.getByRole("status")).toContainText("Step 2 of 8");
  await expect(section.locator(".mc-connection").first()).toHaveAttribute(
    "data-flow-active",
    "true",
  );
  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Previous" })
    .click();
  await expect(section.getByRole("status")).toContainText("Step 1 of 8");
  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Next" })
    .click();
  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Next" })
    .click();
  await expect(section.getByRole("status")).toContainText("Step 3 of 8");
  await expect(communication).toHaveAttribute("data-flow-active", "true");
  await expect(stm).toHaveAttribute("data-flow-active", "true");
  await expect(
    stm.locator('.mc-node-lines [data-active="true"]'),
  ).toContainText("CommunicationTask");
  const play = section.getByRole("button", { name: "Play" });
  await play.click();
  const pause = section.getByRole("button", { name: "Pause" });
  await expect(pause).toBeVisible();
  await pause.click();
  await expect(section.getByRole("button", { name: "Play" })).toBeVisible();

  await section
    .getByRole("button", { name: "Simulate heartbeat loss" })
    .click();
  await expect(section.getByRole("status")).toContainText("ACTIVE → FAULT");
  await expect(section.locator(".mc-fault-branch strong")).toHaveAttribute(
    "data-current",
    "true",
  );
  await expect(
    section.locator('.mc-task-card[data-flow-active="true"]'),
  ).toContainText("SafetyTask");
  await section.getByRole("button", { name: "Reset" }).click();
  await expect(section.getByRole("status")).toContainText("Step 1 of 8");
  await expect(section.getByRole("status")).toContainText(
    "no data is transmitted",
  );

  await section.locator(".mc-future summary").click();
  await expect(section.locator(".mc-future-content")).toContainText("IMUTask");
  await expect(section.locator(".mc-future-content")).toContainText(
    "not implemented",
  );
  await section.locator(".mc-sequence summary").click();
  await expect(section.locator(".mc-sequence li")).toHaveCount(8);
  await expect(
    section.getByRole("heading", { name: "Explicit arming. Latched fault." }),
  ).toBeVisible();
  await expect(section.locator(".mc-safety-caveat")).toContainText(
    "not physically validated",
  );

  await page.getByRole("button", { name: "Español", exact: true }).click();
  await expect(
    section.getByRole("button", { name: "Siguiente" }),
  ).toBeVisible();
  await expect(
    section.getByRole("button", { name: "Simular pérdida de heartbeat" }),
  ).toBeVisible();
  await expect(section).toContainText("La Raspberry Pi procesa visión e IA");
  const overflow = await section.evaluate(
    (element) => element.scrollWidth > element.clientWidth,
  );
  expect(overflow).toBe(false);
  const viewport = page.viewportSize();
  await page.setViewportSize({ width: 320, height: 800 });
  expect(
    await section.evaluate(
      (element) => element.scrollWidth <= element.clientWidth,
    ),
  ).toBe(true);
  if (viewport) await page.setViewportSize(viewport);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(section.getByRole("button", { name: "Play" })).toHaveCount(0);
  await expect(section.locator(".mc-reduced-note")).toBeVisible();
  await expect(
    section.getByRole("button", { name: "Siguiente" }),
  ).toBeEnabled();

  const nav = page.getByRole("navigation", { name: "Navegación principal" });
  if (info.project.name !== "desktop")
    await page.getByRole("button", { name: "Abrir navegación" }).click();
  await nav.getByRole("link", { name: "FreeRTOS", exact: true }).click();
  await expect(page).toHaveURL(/#motion-control$/);
  await expect(page.locator('nav a[href="#motion-control"]')).toHaveAttribute(
    "aria-current",
    "location",
  );
  const links = await page
    .locator(".site-header a:visible")
    .evaluateAll((elements) =>
      elements.map((element) => {
        const rect = element.getBoundingClientRect();
        return { left: rect.left, right: rect.right, width: window.innerWidth };
      }),
    );
  expect(
    links.every((rect) => rect.left >= 0 && rect.right <= rect.width),
  ).toBe(true);
  expect(
    connections.filter((url) => new URL(url).hostname !== "127.0.0.1"),
  ).toEqual([]);
  await section.screenshot({
    path: `test-results/${info.project.name}-motion-control.png`,
  });
});

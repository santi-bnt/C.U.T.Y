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
    section.getByText(`In development \u2014 Hardware integration pending`),
  ).toBeVisible();
  await expect(section.locator(".mc-status-strip")).toContainText(
    "preliminary dry-run",
  );

  const diagram = section.locator(".mc-diagram");
  const diagramNodes = diagram.locator(".mc-node");
  await expect(diagramNodes).toHaveCount(3);
  const diagramSurfaces = await diagramNodes.evaluateAll((nodes) =>
    nodes.map((node) => ({
      background: getComputedStyle(node).backgroundColor,
      border: getComputedStyle(node).borderTopColor,
      text: getComputedStyle(node).color,
    })),
  );
  expect(new Set(diagramSurfaces.map((node) => node.background))).toEqual(
    new Set(["rgb(248, 245, 242)"]),
  );
  expect(new Set(diagramSurfaces.map((node) => node.border))).toEqual(
    new Set(["rgb(231, 226, 220)"]),
  );
  expect(new Set(diagramSurfaces.map((node) => node.text))).toEqual(
    new Set(["rgb(23, 23, 23)"]),
  );
  const pi = diagram.getByRole("button", { name: /Raspberry Pi 5/ });
  const stm = diagram.getByRole("button", { name: /STM32F401 \+ FreeRTOS/ });
  const servos = diagram.getByRole("button", { name: /3 \u00d7 MG996R/ });
  const selectedCount = () =>
    diagramNodes.evaluateAll(
      (nodes) => nodes.filter((node) => node.getAttribute("aria-pressed") === "true").length,
    );
  await expect(pi).toHaveAttribute("aria-pressed", "false");
  await expect(stm).toHaveAttribute("aria-pressed", "false");
  await expect(servos).toHaveAttribute("aria-pressed", "false");
  expect(await selectedCount()).toBe(0);
  await stm.click();
  await expect(stm).toHaveAttribute("aria-pressed", "true");
  await expect(stm).toHaveCSS("border-top-color", "rgb(255, 106, 0)");
  await expect(pi).toHaveAttribute("aria-pressed", "false");
  await expect(servos).toHaveAttribute("aria-pressed", "false");
  await expect(pi).toHaveCSS("border-top-color", "rgb(231, 226, 220)");
  expect(await selectedCount()).toBe(1);
  await servos.click();
  await expect(servos).toHaveAttribute("aria-pressed", "true");
  await expect(servos).toHaveCSS("border-top-color", "rgb(255, 106, 0)");
  await expect(stm).toHaveAttribute("aria-pressed", "false");
  await expect(stm).toHaveCSS("border-top-color", "rgb(231, 226, 220)");
  expect(await selectedCount()).toBe(1);
  await pi.focus();
  await page.keyboard.press("Enter");
  await expect(pi).toHaveAttribute("aria-pressed", "true");
  await expect(servos).toHaveAttribute("aria-pressed", "false");
  expect(await selectedCount()).toBe(1);

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
  for (const name of ["ServoControlTask", "SafetyTask", "DiagnosticsTask"]) {
    const card = tasks.getByRole("button", { name: new RegExp(name) });
    await card.click();
    await expect(card).toHaveAttribute("aria-pressed", "true");
    await expect(section.locator(".mc-task-details h4")).toHaveText(name);
    if (name === "SafetyTask")
      await expect(section.locator(".mc-task-details")).toContainText("RESET");
  }
  await tasks.getByRole("button", { name: /CommunicationTask/ }).click();

  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Next" })
    .click();
  await expect(section.getByRole("status")).toContainText("Step 2 of 8");
  expect(await selectedCount()).toBe(1);
  await expect(section.locator(".mc-connection").first()).toHaveAttribute(
    "data-flow-active",
    "true",
  );
  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Previous" })
    .click();
  await expect(section.getByRole("status")).toContainText("Step 1 of 8");
  expect(await selectedCount()).toBe(1);
  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Next" })
    .click();
  await section
    .getByRole("group", { name: "Simulation controls" })
    .getByRole("button", { name: "Next" })
    .click();
  await expect(section.getByRole("status")).toContainText("Step 3 of 8");
  expect(await selectedCount()).toBe(1);
  await expect.poll(() => stm.evaluate((node) => getComputedStyle(node).backgroundColor)).toBe("rgb(248, 245, 242)");
  await expect(stm).toHaveCSS("border-top-color", "rgb(231, 226, 220)");
  await expect(pi).toHaveCSS("border-top-color", "rgb(255, 106, 0)");
  await expect(communication).toHaveAttribute("data-flow-active", "true");
  await expect(stm).toHaveAttribute("data-flow-active", "true");
  await expect(
    stm.locator('.mc-node-lines [data-active="true"]'),
  ).toContainText("CommunicationTask");
  const play = section.getByRole("button", { name: "Play" });
  await play.click();
  const pause = section.getByRole("button", { name: "Pause" });
  await expect(pause).toBeVisible();
  expect(await selectedCount()).toBe(1);
  await pause.click();
  await expect(section.getByRole("button", { name: "Play" })).toBeVisible();
  expect(await selectedCount()).toBe(1);

  await section
    .getByRole("button", { name: "Simulate heartbeat loss" })
    .click();
  await expect(section.getByRole("status")).toContainText(`ACTIVE \u2192 FAULT`);
  await expect(section.locator(".mc-fault-branch strong")).toHaveAttribute(
    "data-current",
    "true",
  );
  await expect(
    section.locator('.mc-task-card[data-flow-active="true"]'),
  ).toContainText("SafetyTask");
  await section.getByRole("button", { name: "Reset" }).click();
  expect(await selectedCount()).toBe(1);
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

  await page.getByRole("button", { name: `Espa\u00f1ol`, exact: true }).click();
  await expect(
    section.getByRole("button", { name: "Siguiente" }),
  ).toBeVisible();
  await expect(
    section.getByRole("button", { name: `Simular p\u00e9rdida de heartbeat` }),
  ).toBeVisible();
  await expect(section).toContainText(`La Raspberry Pi procesa visi\u00f3n e IA`);
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

  const nav = page.getByRole("navigation", { name: `Navegaci\u00f3n principal` });
  if (info.project.name !== "desktop")
    await page.getByRole("button", { name: `Abrir navegaci\u00f3n` }).click();
  await nav.getByRole("link", { name: "FreeRTOS", exact: true }).click();
  await expect(page).toHaveURL(/#motion-control$/);
  await expect(page.locator('nav a[href="#motion-control"]')).toHaveAttribute(
    "aria-current",
    "location",
  );
  if (info.project.name !== "desktop")
    await page.getByRole("button", { name: `Abrir navegaci\u00f3n` }).click();
  await nav.getByRole("link", { name: "DSP / FIR", exact: true }).click();
  await expect(page).toHaveURL(/#dsp-filters$/);
  await expect(page.locator('nav a[href="#dsp-filters"]')).toHaveAttribute(
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

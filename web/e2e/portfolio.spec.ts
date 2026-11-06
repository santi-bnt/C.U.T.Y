import { expect, test } from "@playwright/test";

async function chapter(
  page: import("@playwright/test").Page,
  id: string,
  index: number,
) {
  await page.locator("#" + id).evaluate((element) =>
    window.scrollTo({
      top: element.getBoundingClientRect().top + window.scrollY,
      behavior: "instant",
    }),
  );
  await expect(page.locator(".scene-layer")).toHaveAttribute(
    "data-chapter",
    String(index),
  );
}

test("persistent product story, original display, manual controls and translation", async ({
  page,
}, info) => {
  const errors: string[] = [];
  let modelRequests = 0;
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("request", (request) => {
    if (request.url().includes("/models/cuty.glb")) modelRequests++;
  });
  await page.goto("/");
  if (
    await page
      .getByRole("button", { name: "Skip intro", exact: true })
      .isVisible()
  )
    await page.getByRole("button", { name: "Skip intro", exact: true }).click();
  await expect(page.getByText("Loading real GLB…")).toBeHidden({
    timeout: 30000,
  });
  await expect(page.getByRole("alert")).toHaveCount(0);
  if (info.project.name !== "desktop") {
    const menu = page.getByRole("button", { name: "Toggle navigation" });
    await menu.click();
    await expect(menu).toHaveAttribute("aria-expanded", "true");
    const navigation = page.getByRole("navigation", {
      name: "Main navigation",
    });
    await expect(navigation.getByRole("link")).toHaveCount(7);
    await navigation.locator('a[href="#pcb-design"]').click();
    await expect(menu).toHaveAttribute("aria-expanded", "false");
    await chapter(page, "home", 0);
  }
  await page
    .locator("canvas")
    .evaluate((canvas) =>
      canvas.setAttribute("data-persistence-check", "original"),
    );
  await page.screenshot({ path: `test-results/${info.project.name}-hero.png` });
  for (const [id, index] of [
    ["companion", 1],
    ["intelligence", 2],
    ["hardware-explorer", 3],
    ["pcb-design", 4],
    ["wiring", 5],
    ["development", 6],
    ["live", 7],
  ] as const) {
    await chapter(page, id, index);
    await expect(page.locator(".scene-layer canvas")).toHaveCount(1);
    await expect(page.locator(".scene-layer canvas")).toHaveAttribute(
      "data-persistence-check",
      "original",
    );
    if (id === "intelligence") {
      await expect(page.locator(".scene-layer canvas")).toHaveAttribute(
        "data-shot",
        "2",
      );
      await page.getByRole("button", { name: "Happy", exact: true }).click();
      await expect(page.locator(".face-screen")).toHaveClass(/happy/);
      await expect(page.locator(".face-original img")).toHaveAttribute(
        "src",
        /face\/happy\.webp$/,
      );
      await page
        .getByRole("button", { name: "Animate mouth", exact: true })
        .click();
      await expect(page.locator(".face-screen")).toHaveClass(/talking/);
      await page
        .getByRole("button", { name: "Stop mouth", exact: true })
        .click();
      await page.screenshot({
        path: `test-results/${info.project.name}-expressions.png`,
      });
    }
  }
  expect(modelRequests).toBe(1);
  await expect(
    page.getByRole("button", { name: "Dashboard not configured" }),
  ).toBeDisabled();
  await chapter(page, "home", 0);
  await expect(page.locator(".scene-layer")).toHaveCSS("opacity", "0");
  await expect(
    page.getByRole("button", { name: "Explore in 3D", exact: true }),
  ).toBeHidden();
  await chapter(page, "companion", 1);
  await chapter(page, "companion", 1);
  await page
    .getByRole("button", { name: "Explore in 3D", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Interactive robot explorer" }),
  ).toBeVisible();
  for (const name of ["Front", "Side", "Top", "Isometric", "LCD"]) {
    const button = page
      .locator(".explore-panel")
      .getByRole("button", { name, exact: true });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
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
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator(".scene-layer canvas")).toHaveAttribute(
    "data-shot",
    "1",
  );
  await page.getByRole("button", { name: "Español", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(
    page.getByText("Una mente curiosa.", { exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(
    await page
      .locator('a[href^="#"]')
      .evaluateAll((links) =>
        links
          .map((a) => a.getAttribute("href")!)
          .filter((href) => href.length > 1 && !document.querySelector(href)),
      ),
  ).toEqual([]);
  expect(errors).toEqual([]);
});

test("actual PCB inspection, electrical search, filters and source downloads", async ({
  page,
}, info) => {
  await page.goto("/");
  if (
    await page
      .getByRole("button", { name: "Skip intro", exact: true })
      .isVisible()
  )
    await page.getByRole("button", { name: "Skip intro", exact: true }).click();
  await chapter(page, "pcb-design", 4);
  await expect(page.locator(".scene-layer")).toHaveCSS("opacity", "0");
  const board = page.locator(".pcb-canvas");
  await expect(board.locator("image")).toHaveAttribute(
    "href",
    /carrier-front\.png$/,
  );
  await page.getByLabel("Select component", { exact: true }).selectOption("U1");
  await expect(page.locator(".pcb-details h3")).toHaveText("BlackPill F401CC");
  await expect(page.locator(".pcb-details")).toContainText("29 / PA3");
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await expect(board.locator("image")).toHaveAttribute(
    "href",
    /carrier-back\.png$/,
  );
  await page.getByRole("button", { name: "Zoom PCB in", exact: true }).click();
  await expect
    .poll(async () =>
      Number((await board.getAttribute("viewBox"))!.split(" ")[2]),
    )
    .toBeLessThan(60);
  await page
    .getByRole("button", { name: "Reset PCB view", exact: true })
    .click();
  await expect
    .poll(async () =>
      Number((await board.getAttribute("viewBox"))!.split(" ")[2]),
    )
    .toBe(100);
  await page
    .getByRole("button", { name: "Select PCB component J1", exact: true })
    .click();
  await expect(page.locator(".pcb-details h3")).toHaveText("XT60 BAT 3S");
  await page.screenshot({ path: `test-results/${info.project.name}-pcb.png` });
  await page
    .getByRole("button", { name: "3D mechanical reference", exact: true })
    .click();
  await expect(page.locator(".engineering-viewport.pcb canvas")).toHaveCount(1);
  await page.getByRole("button", { name: "Back 3D", exact: true }).click();
  await page.getByRole("button", { name: "Front 3D", exact: true }).click();
  await expect(page.locator(".scene-layer canvas")).toHaveCount(1);
  for (const file of [
    "carrier-front.png",
    "carrier-back.png",
    "carrier-schematic.pdf",
    "carrier.kicad_pcb",
    "carrier.kicad_sch",
    "carrier-bom.csv",
    "carrier-gerbers.zip",
    "carrier-project.zip",
  ]) {
    const response = await page.request.get("/engineering/" + file);
    expect(response.status()).toBe(200);
    expect((await response.body()).length).toBeGreaterThan(100);
  }
  await chapter(page, "wiring", 5);
  await page
    .locator(".wire-filters")
    .getByRole("button", { name: "UART", exact: true })
    .click();
  await expect(page.locator(".connection-table tbody tr")).toHaveCount(2);
  await page
    .getByRole("searchbox", { name: "Search connections" })
    .fill("BCM 14");
  await expect(page.locator(".connection-table tbody tr")).toHaveCount(1);
  await expect(page.locator(".connection-table tbody")).toContainText(
    "STM32 RX",
  );
  await page.getByRole("searchbox", { name: "Search connections" }).fill("");
  await page
    .locator(".wire-filters")
    .getByRole("button", { name: "Power", exact: true })
    .click();
  const buck = page
    .locator(".spatial-parts")
    .getByRole("button", { name: "Adjustable servo buck", exact: true });
  await buck.click();
  await expect(page.locator(".wiring-detail")).toContainText(
    "current remain unverified",
  );
  await expect(page.locator(".connection-table tbody")).toContainText("6.0 V");
  await page.locator("#wiring").evaluate((el) =>
    window.scrollTo({
      top: el.getBoundingClientRect().top + scrollY,
      behavior: "instant",
    }),
  );
  await page.screenshot({
    path: `test-results/${info.project.name}-wiring.png`,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("deep anchors and reduced motion keep the story usable", async ({
  page,
}) => {
  await page.goto("/#intelligence");
  await expect(page.locator(".scene-layer")).toHaveAttribute(
    "data-chapter",
    "2",
  );
  await expect(page.locator(".scene-layer canvas")).toHaveAttribute(
    "data-shot",
    "2",
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  if (
    await page
      .getByRole("button", { name: "Skip intro", exact: true })
      .isVisible()
  )
    await page.getByRole("button", { name: "Skip intro", exact: true }).click();
  await chapter(page, "companion", 1);
  await page
    .getByRole("button", { name: "Explore in 3D", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Auto-rotate", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Back to the story", exact: true })
    .click();
  await page.route("**/models/cuty.glb*", (route) =>
    route.fulfill({ status: 404, body: "Model missing" }),
  );
  await page.reload();
  await expect(page.getByRole("alert")).toContainText(
    "web/public/models/cuty.glb",
    { timeout: 30000 },
  );
  await expect(
    page.getByRole("link", { name: "Technical Architecture", exact: true }),
  ).toHaveAttribute("href", "#architecture");
});

test("kinetic opening, named-part demos, assembly imagery and spatial connections", async ({
  page,
}, info) => {
  await page.goto("/");
  await expect(
    page.getByRole("dialog", { name: "C.U.T.Y. introduction" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Skip intro", exact: true }),
  ).toBeFocused();
  await page.screenshot({
    path: `test-results/${info.project.name}-intro.png`,
  });
  await page.getByRole("button", { name: "Skip intro", exact: true }).click();
  await expect(page.locator(".intro-sequence")).toHaveCount(0);
  await page.locator(".hero-replay").click();
  await expect(
    page.getByRole("dialog", { name: "C.U.T.Y. introduction" }),
  ).toBeVisible();
  await page.waitForTimeout(2050);
  const introBounds = await page.locator(".intro-mask").last().boundingBox();
  expect(introBounds!.x).toBeGreaterThanOrEqual(0);
  expect(introBounds!.x + introBounds!.width).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  await page.screenshot({
    path: `test-results/${info.project.name}-replayed-intro.png`,
  });
  await page.keyboard.press("Escape");
  await expect(page.locator(".intro-sequence")).toHaveCount(0);
  await expect(page.locator(".hero-replay")).toBeFocused();
  const ink = await page
    .locator(".hero-letter-mask")
    .nth(6)
    .evaluate((mask) => {
      const letter = mask.querySelector(".hero-letter")!;
      const style = getComputedStyle(letter);
      const ctx = document.createElement("canvas").getContext("2d")!;
      ctx.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
      return {
        right:
          letter.getBoundingClientRect().left +
          ctx.measureText("Y").actualBoundingBoxRight,
        clip: mask.getBoundingClientRect().right,
      };
    });
  expect(ink.right).toBeLessThanOrEqual(ink.clip + 1);

  await expect(page.getByText("Loading real GLB…")).toBeHidden({
    timeout: 30000,
  });
  await chapter(page, "companion", 1);
  await page
    .getByRole("button", { name: "Explore in 3D", exact: true })
    .click();
  for (const name of [
    "Exploded view",
    "Inside",
    "Assembled",
    "Wave demo",
    "Look demo",
  ]) {
    const button = page.getByRole("button", { name, exact: true });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
  }
  await page.keyboard.press("Escape");
  await page
    .locator("#assembly")
    .evaluate((e) => e.scrollIntoView({ behavior: "instant" }));
  await page
    .getByRole("button", { name: "Next assembly step", exact: true })
    .click();
  await expect(page.locator(".assembly-caption h3")).toHaveText(
    "Made in layers",
  );
  await expect(page.locator(".assembly-image img")).toHaveAttribute(
    "src",
    /imprime.webp$/,
  );
  await page.screenshot({
    path: `test-results/${info.project.name}-assembly.png`,
  });
  await page
    .locator("#wiring")
    .evaluate((e) => e.scrollIntoView({ behavior: "instant" }));
  await page.locator(".engineering-viewport.wiring").scrollIntoViewIfNeeded();
  await expect(page.locator(".engineering-viewport.wiring canvas")).toHaveCount(
    1,
  );
  await page
    .locator(".spatial-parts")
    .getByRole("button", { name: "ReSpeaker 2-Mics V2.0", exact: true })
    .click();
  await expect(page.locator(".wiring-detail")).toContainText(
    "Confirmed I2C/I2S",
  );
  await expect(page.locator(".connection-table tbody .confirmed")).toHaveCount(
    11,
  );
  await expect(page.locator(".connection-table tbody")).toContainText("MCLK");
  await expect(page.locator(".connection-table tbody")).toContainText(
    "AUD_RST",
  );
  await expect(page.locator(".connection-table tbody")).toContainText("Pi 1");
  await expect(page.locator(".connection-table tbody")).toContainText("Pi 4");
  await expect(page.locator(".connection-table tbody")).toContainText("Pi 6");
  await page.getByRole("button", { name: "2D overview", exact: true }).click();
  await expect(page.locator(".wiring-diagram")).toHaveCount(1);
  await page
    .getByRole("button", { name: "3D simulation", exact: true })
    .click();
  await page.locator(".engineering-viewport.wiring").scrollIntoViewIfNeeded();
  await expect(page.locator(".engineering-viewport.wiring canvas")).toHaveCount(
    1,
  );
  const response = await page.request.get("/assembly/nido-print-stl.zip");
  expect(response.status()).toBe(200);
  expect((await response.body()).length).toBeGreaterThan(1000000);
});

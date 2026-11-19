import { expect, test } from "@playwright/test";

test("DSP controls update the selected FIR and real plotted data", async ({ page }, info) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") pageErrors.push(message.text());
  });
  await page.goto("/#dsp-filters", { waitUntil: "domcontentloaded" });
  const section = page.locator("#dsp-filters");
  await section.waitFor({ state: "attached", timeout: 15_000 });
  await section.scrollIntoViewIfNeeded();
  expect(await section.evaluate((node) => node.nextElementSibling?.id)).toBe("about");
  await expect(section).toHaveCSS("background-color", "rgb(23, 23, 23)");
  await expect(section.getByRole("heading", { name: "Digital Signal Processing / FIR Filters" })).toBeVisible();
  await expect(page.locator('nav a[href="#dsp-filters"]')).toHaveAttribute("aria-current", "location");

  const head = section.getByRole("button", { name: /Head tracking/ });
  const speech = section.getByRole("button", { name: /Speech/ });
  await expect(head).toHaveAttribute("aria-pressed", "true");
  await expect(section.locator(".dsp-facts")).toContainText("5 / 4");
  await expect(section.locator(".dsp-facts")).toContainText("50 Hz");
  await expect(section.locator(".dsp-flow")).toContainText("FaceTracker");
  const response = section.locator(".dsp-response svg");
  const headResponse = await response.locator(".dsp-filtered").getAttribute("d");
  await expect(response).toHaveAttribute("data-sample-rate", "50");
  await expect(response).toHaveAttribute("data-frequency-count", "129");

  const timePlot = section.locator(".dsp-signal-plot").nth(0);
  const spectrumPlot = section.locator(".dsp-signal-plot").nth(1);
  const comparePaths = timePlot.locator("path.dsp-original");
  await expect(comparePaths).toHaveCount(1);
  await expect(timePlot.locator("path.dsp-filtered")).toHaveCount(1);
  const compareOriginal = await comparePaths.getAttribute("d");

  await section.getByRole("button", { name: "Original" }).click();
  await expect(section.getByRole("button", { name: "Original" })).toHaveAttribute("aria-pressed", "true");
  await expect(timePlot.locator("path.dsp-original")).toHaveCount(1);
  await expect(timePlot.locator("path.dsp-filtered")).toHaveCount(0);
  await expect(spectrumPlot.locator("path.dsp-original")).toHaveCount(1);
  await expect(spectrumPlot.locator("path.dsp-filtered")).toHaveCount(0);
  expect(await timePlot.locator("path.dsp-original").getAttribute("d")).toBe(compareOriginal);

  await section.getByRole("button", { name: "Filtered" }).click();
  await expect(timePlot.locator("path.dsp-original")).toHaveCount(0);
  await expect(timePlot.locator("path.dsp-filtered")).toHaveCount(1);
  await expect(spectrumPlot.locator("path.dsp-original")).toHaveCount(0);
  await expect(spectrumPlot.locator("path.dsp-filtered")).toHaveCount(1);
  const filteredPath = await timePlot.locator("path.dsp-filtered").getAttribute("d");
  expect(filteredPath).not.toBe(compareOriginal);

  const compareButton = section.getByRole("button", { name: "Compare" });
  await compareButton.click();
  await expect(timePlot.locator("path.dsp-original")).toHaveCount(1);
  await expect(timePlot.locator("path.dsp-filtered")).toHaveCount(1);
  await expect(timePlot.locator(".dsp-legend-original")).toBeVisible();
  await expect(timePlot.locator(".dsp-legend-filtered")).toBeVisible();

  await speech.click();
  await expect(speech).toHaveAttribute("aria-pressed", "true");
  await expect(head).toHaveAttribute("aria-pressed", "false");
  await expect(section.locator(".dsp-facts")).toContainText("511 / 510");
  await expect(section.locator(".dsp-facts")).toContainText("16 kHz");
  await expect(section.locator(".dsp-flow")).toContainText("ReSpeaker");
  await expect(section.locator(".dsp-flow")).toContainText("Gemini Live");
  await expect(response).toHaveAttribute("data-sample-rate", "16000");
  const speechResponse = await response.locator(".dsp-filtered").getAttribute("d");
  expect(speechResponse).not.toBe(headResponse);
  await expect(section.locator(".dsp-caption")).toContainText("150");

  const slider = section.getByRole("slider");
  await expect(slider).toHaveAttribute("aria-valuetext", "1000 Hz");
  const initialInput = await timePlot.locator("path.dsp-original").getAttribute("d");
  const initialFiltered = await timePlot.locator("path.dsp-filtered").getAttribute("d");
  const initialSpectrum = await spectrumPlot.locator("path.dsp-original").getAttribute("d");
  const responseBeforeTone = await response.locator(".dsp-filtered").getAttribute("d");
  await slider.focus();
  await page.keyboard.press("ArrowRight");
  await expect(section.locator(".dsp-slider output")).toHaveText("1050 Hz");
  await expect(slider).toHaveAttribute("aria-valuetext", "1050 Hz");
  const keyboardInput = await timePlot.locator("path.dsp-original").getAttribute("d");
  const keyboardFiltered = await timePlot.locator("path.dsp-filtered").getAttribute("d");
  const keyboardSpectrum = await spectrumPlot.locator("path.dsp-original").getAttribute("d");
  expect(keyboardInput).not.toBe(initialInput);
  expect(keyboardFiltered).not.toBe(initialFiltered);
  expect(keyboardSpectrum).not.toBe(initialSpectrum);

  const sliderBox = await slider.boundingBox();
  expect(sliderBox).not.toBeNull();
  if (sliderBox) {
    const currentValue = Number(await slider.inputValue());
    const min = Number(await slider.getAttribute("min"));
    const max = Number(await slider.getAttribute("max"));
    const thumbInset = 8;
    const thumbTravel = sliderBox.width - thumbInset * 2;
    const currentThumbX = sliderBox.x + thumbInset + ((currentValue - min) / (max - min)) * thumbTravel;
    await page.mouse.move(currentThumbX, sliderBox.y + sliderBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(sliderBox.x + thumbInset + thumbTravel * 0.82, sliderBox.y + sliderBox.height / 2, { steps: 8 });
    await page.mouse.up();
  }
  await expect.poll(() => slider.getAttribute("aria-valuetext")).not.toBe("1050 Hz");
  const mouseInput = await timePlot.locator("path.dsp-original").getAttribute("d");
  const mouseSpectrum = await spectrumPlot.locator("path.dsp-original").getAttribute("d");
  expect(mouseInput).not.toBe(keyboardInput);
  expect(mouseSpectrum).not.toBe(keyboardSpectrum);
  expect(await response.locator(".dsp-filtered").getAttribute("d")).toBe(responseBeforeTone);

  await page.getByRole("button", { name: `Espa\u00f1ol`, exact: true }).click();
  await expect(section.getByRole("button", { name: /Voz/ })).toHaveAttribute("aria-pressed", "true");
  await expect(section.getByRole("button", { name: "Comparar" })).toHaveAttribute("aria-pressed", "true");
  await section.getByRole("button", { name: "Original", exact: true }).click();
  await expect(timePlot.locator("path.dsp-filtered")).toHaveCount(0);
  await section.getByRole("button", { name: "Filtrada", exact: true }).click();
  await expect(timePlot.locator("path.dsp-original")).toHaveCount(0);
  await section.getByRole("button", { name: "Comparar", exact: true }).click();
  await expect(timePlot.locator("path.dsp-original")).toHaveCount(1);
  await expect(timePlot.locator("path.dsp-filtered")).toHaveCount(1);
  await section.screenshot({ path: `test-results/${info.project.name}-digital-signal-processing.png` });

  const headSpanish = section.getByRole("button", { name: /Seguimiento de cabeza/ });
  await headSpanish.click();
  await expect(headSpanish).toHaveAttribute("aria-pressed", "true");
  await expect(response).toHaveAttribute("data-sample-rate", "50");
  await expect(section.locator(".dsp-flow")).toContainText("FaceTracker");
  const speechSpanish = section.getByRole("button", { name: /Voz/ });
  await speechSpanish.click();
  await expect(speechSpanish).toHaveAttribute("aria-pressed", "true");
  await expect(response).toHaveAttribute("data-sample-rate", "16000");
  await expect(section.locator(".dsp-flow")).toContainText("ReSpeaker");

  expect(await section.evaluate((node) => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
  await page.setViewportSize({ width: 320, height: 780 });
  expect(await section.evaluate((node) => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
  await expect(slider).toBeVisible();
  const nonFinitePaths = await section.locator("svg path[d]").evaluateAll((paths) =>
    paths.filter((path) => /NaN|Infinity/.test(path.getAttribute("d") ?? "")).length,
  );
  expect(nonFinitePaths).toBe(0);
  expect(pageErrors).toEqual([]);
});

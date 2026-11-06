import { describe, expect, it, vi } from "vitest";
import { atlasFrame, drawFaceFrame } from "./faceFrames";

describe("display frame boundary", () => {
  it("draws the selected original atlas frame into the physical display resolution", () => {
    const image = {} as CanvasImageSource;
    const frame = atlasFrame(image, 39);
    const context = { clearRect: vi.fn(), drawImage: vi.fn() };
    drawFaceFrame(context as unknown as CanvasRenderingContext2D, frame);
    expect(context.drawImage).toHaveBeenCalledWith(
      image,
      1920,
      2240,
      480,
      320,
      0,
      0,
      480,
      320,
    );
    expect(atlasFrame(image, -2).source.x).toBe(0);
  });
  it("accepts a decoded full live frame through the same pixel sink without a transport", () => {
    const image = {} as CanvasImageSource;
    const context = { clearRect: vi.fn(), drawImage: vi.fn() };
    drawFaceFrame(context as unknown as CanvasRenderingContext2D, {
      image,
      source: { x: 0, y: 0, width: 480, height: 320 },
    });
    expect(context.clearRect).toHaveBeenCalledWith(0, 0, 480, 320);
    expect(context.drawImage).toHaveBeenCalledWith(
      image,
      0,
      0,
      480,
      320,
      0,
      0,
      480,
      320,
    );
  });
});

/** Display pixels are independent of telemetry, storage and authentication.
 * A future transport owns decoding/closing ImageBitmaps; consumers only draw.
 * No socket, endpoint or connection attempt is created by this module.
 */
export interface FaceFrame {
  image: CanvasImageSource;
  source: { x: number; y: number; width: number; height: number };
}
export interface FaceFrameSource {
  readonly mode: "demo" | "live";
  subscribe(receive: (frame: FaceFrame) => void): () => void;
}
export function atlasFrame(image: CanvasImageSource, frame: number): FaceFrame {
  const index = Math.max(0, Math.min(39, Math.trunc(frame)));
  return {
    image,
    source: {
      x: (index % 5) * 480,
      y: Math.floor(index / 5) * 320,
      width: 480,
      height: 320,
    },
  };
}
/** Both atlas playback and a future decoded stream feed the same pixel sink. */
export function drawFaceFrame(
  context: CanvasRenderingContext2D,
  frame: FaceFrame,
) {
  const { x, y, width, height } = frame.source;
  context.clearRect(0, 0, 480, 320);
  context.drawImage(frame.image, x, y, width, height, 0, 0, 480, 320);
}

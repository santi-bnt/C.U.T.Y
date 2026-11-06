import { useEffect, useMemo } from "react";
import { useLoader, useThree } from "@react-three/fiber";
import {
  CanvasTexture,
  ImageLoader,
  LinearFilter,
  SRGBColorSpace,
} from "three";
import { atlasFrame, drawFaceFrame } from "../communication/faceFrames";
import { useFaceSimulation } from "../state/FaceSimulation";
import { useFaceFrameSource } from "../state/FaceFrames";

/** The 3D LCD and the face lab display the same original Python-rendered frame. */
export function useFaceTexture() {
  const { expression, frame } = useFaceSimulation();
  const source = useFaceFrameSource();
  const atlas = useLoader(
    ImageLoader,
    `${import.meta.env.BASE_URL}face/${expression}.webp`,
  );
  const invalidate = useThree((state) => state.invalidate);
  const { canvas, texture } = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 480;
    canvas.height = 320;
    const texture = new CanvasTexture(canvas);
    texture.colorSpace = SRGBColorSpace;
    texture.generateMipmaps = false;
    texture.minFilter = LinearFilter;
    return { canvas, texture };
  }, []);
  useEffect(() => {
    if (source?.mode === "live") return;
    drawFaceFrame(canvas.getContext("2d")!, atlasFrame(atlas, frame));
    // Three.js requires an imperative upload flag on this owned texture.
    // eslint-disable-next-line react-hooks/immutability
    texture.needsUpdate = true;
    invalidate();
  }, [atlas, canvas, frame, texture, invalidate, source]);
  useEffect(() => {
    if (source?.mode !== "live") return;
    return source.subscribe((incoming) => {
      drawFaceFrame(canvas.getContext("2d")!, incoming);
      texture.needsUpdate = true;
      invalidate();
    });
  }, [source, canvas, texture, invalidate]);
  useEffect(() => () => texture.dispose(), [texture]);
  return texture;
}

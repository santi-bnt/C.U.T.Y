import { Box3, Vector3, type Object3D } from "three";
export function measureModel(scene: Object3D) {
  const box = new Box3().setFromObject(scene);
  const size = box.getSize(new Vector3());
  const center = box.getCenter(new Vector3());
  if (!Number.isFinite(size.y) || size.y <= 0)
    throw new Error("Invalid model bounds");
  return { size, center, scale: 3 / size.y };
}
export const cameraViews = {
  front: [0, 1.5, 6.8],
  side: [6.8, 1.5, 0],
  top: [0.001, 8, 0.001],
  iso: [4, 3.2, 6],
  display: [0, 2.2, 3.5],
} as const;
export type CameraView = keyof typeof cameraViews;

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
  front: [6.8, 1.5, 0],
  side: [0, 1.5, 6.8],
  top: [0.001, 8, 0.001],
  iso: [5, 3.2, 5],
} as const;
export type CameraView = keyof typeof cameraViews;

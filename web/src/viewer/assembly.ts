import { Vector3, type Object3D, Mesh } from "three";
export type AssemblyView = "assembled" | "interior" | "exploded";
export type PoseDemo = "none" | "wave" | "look";
export function explosionOffset(name: string) {
  if (/^H[1-8]_/.test(name))
    return new Vector3(
      name.includes("Front") ? 55 : name.includes("Back") ? -55 : 0,
      65,
      name.includes("Back") ? -45 : 45,
    );
  if (/^S[1-4]_/.test(name))
    return new Vector3(0, 0, name.includes("Back") ? -100 : 100);
  if (/^A[1-6]_/.test(name))
    return new Vector3(name.endsWith("_L") ? -75 : 75, 15, 0);
  if (/^B[13]_/.test(name))
    return new Vector3(0, -22, name.includes("Drawer") ? -85 : 30);
  if (/^(pcb_|respeaker_|fuse_)/.test(name)) return new Vector3(0, 8, 48);
  if (/^pi5_/.test(name)) return new Vector3(0, 8, -55);
  return new Vector3();
}
const axis = new Vector3(),
  pivot = new Vector3(),
  rotated = new Vector3();
/** Display-only rigid part movement. No hardware commands or validated joint limits. */
export function updateAssembly(
  object: Object3D,
  view: AssemblyView,
  pose: PoseDemo,
  time: number,
) {
  object.traverse((child) => {
    if (!(child instanceof Mesh)) return;
    child.visible = !(
      view === "interior" && /^(H[1-36-8]_|S[1-4]_|B[13]_)/.test(child.name)
    );
    child.position.set(0, 0, 0);
    child.rotation.set(0, 0, 0);
    if (view === "exploded") child.position.copy(explosionOffset(child.name));
    if (view !== "assembled" || pose === "none") return;
    let angle = 0;
    if (
      pose === "look" &&
      /^(H[1-8]_|lcd_|camera_|servo_head_case)/.test(child.name)
    ) {
      angle = Math.sin(time * 0.9) * 0.38;
      axis.set(0, 1, 0);
      pivot.set(0, 212, 0);
    }
    if (pose === "wave" && /^(A[246]_|servo_arm_R_spline)/.test(child.name)) {
      angle = -0.85 + Math.sin(time * 4) * 0.16;
      axis.set(1, 0, 0);
      pivot.set(0, 176, -6);
    }
    if (angle) {
      child.quaternion.setFromAxisAngle(axis, angle);
      rotated.copy(pivot).applyQuaternion(child.quaternion);
      child.position.copy(pivot).sub(rotated);
    }
  });
}

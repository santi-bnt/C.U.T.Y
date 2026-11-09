import {
  Box3,
  Float32BufferAttribute,
  Group,
  Mesh,
  MeshBasicMaterial,
  Material,
  MeshStandardMaterial,
  type BufferGeometry,
  type Object3D,
  type Texture,
} from "three";
import nido from "../data/nido.generated.json";
import { themeColor } from "../theme";
import { measureModel } from "./model";
const names = new Set(nido.parts.map((p) => p.name));
const photoWhite = themeColor("--robot-case", "#f4f2ee");
const photoBase = themeColor("--robot-base", "#dfc09a");
const photoGray = themeColor("--robot-gray", "#888a88");
const photoOrange = themeColor("--orange", "#ff6a00");
export const photoPaletteByMaterial: Record<string, string> = {
  S1_Body_Front: photoWhite,
  S2_Body_Back: photoWhite,
  A1_Arm_L: photoWhite,
  A2_Arm_R: photoWhite,
  H1_Head_Front: photoWhite,
  H2_Head_Back: photoWhite,
  B1_Base_Cover: photoBase,
  B3_Battery_Drawer: photoBase,
  B2_Base_Floor: photoGray,
  B4_Gimbal_Post: photoGray,
  K1_Core_Deck: photoGray,
  K2_Core_Spine: photoGray,
  K3_Core_Shoulders: photoGray,
  K5_Power_Rack: photoGray,
  H4_Display_Bars: photoGray,
  H5_Head_Base: photoGray,
  H3_Visor: themeColor("--dark", "#171717"),
  S3_Tummy_Grille: photoOrange,
  S4_USB_Plug: photoOrange,
  A3_Hand_L: photoOrange,
  A4_Hand_R: photoOrange,
  A5_Arm_Cap_L: photoOrange,
  A6_Arm_Cap_R: photoOrange,
  H6_Ear_L: photoOrange,
  H7_Ear_R: photoOrange,
  H8_Antenna: photoOrange,
};
/** Decode quantized attributes before baking transforms; cached loader geometry stays untouched. */
export function worldGeometry(mesh: Mesh) {
  const geometry = mesh.geometry.clone();
  for (const name of ["position", "normal"]) {
    const a = geometry.getAttribute(name);
    if (!a) continue;
    const values = new Float32Array(a.count * 3);
    for (let i = 0; i < a.count; i++) {
      values[i * 3] = a.getX(i);
      values[i * 3 + 1] = a.getY(i);
      values[i * 3 + 2] = a.getZ(i);
    }
    geometry.setAttribute(name, new Float32BufferAttribute(values, 3));
  }
  return geometry.applyMatrix4(mesh.matrixWorld);
}
export function partName(object: Object3D) {
  let current: Object3D | null = object;
  while (current) {
    if (names.has(current.name)) return current.name;
    current = current.parent;
  }
  return object.name;
}
/** Existing LCD glass, front +Z in the supplied Y-up Nido model; no floating face plane. */
export function displayGeometry(source: BufferGeometry) {
  const geometry = source.clone();
  geometry.computeBoundingBox();
  const box = geometry.boundingBox!;
  const p = geometry.attributes.position;
  const index = geometry.index;
  const count = index?.count ?? p.count;
  const height = box.max.y - box.min.y,
    width = Math.min(box.max.x - box.min.x, height * 1.5),
    center = (box.max.x + box.min.x) / 2;
  const uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) {
    uv[i * 2] = (p.getX(i) - center) / width + 0.5;
    uv[i * 2 + 1] = (p.getY(i) - box.min.y) / height;
  }
  geometry.setAttribute("uv", new Float32BufferAttribute(uv, 2));
  geometry.clearGroups();
  let start = 0,
    previous = -1;
  for (let t = 0; t < count; t += 3) {
    const material = [0, 1, 2].every(
      (o) =>
        Math.abs(p.getZ(index ? index.getX(t + o) : t + o) - box.max.z) < 0.02,
    )
      ? 1
      : 0;
    if (material !== previous) {
      if (previous !== -1) geometry.addGroup(start, t - start, previous);
      start = t;
      previous = material;
    }
  }
  geometry.addGroup(start, count - start, previous);
  return geometry;
}
export function prepareRobot(
  source: Object3D,
  faceTexture: Texture,
  wireframe: boolean,
) {
  source.updateMatrixWorld(true);
  const object = new Group();
  const screen = new MeshBasicMaterial({ map: faceTexture, toneMapped: false });
  const materials: Material[] = [screen];
  const geometries: BufferGeometry[] = [];
  source.traverse((child) => {
    if (!(child instanceof Mesh)) return;
    const name = partName(child);
    let geometry = worldGeometry(child);
    const sourceMaterials = Array.isArray(child.material)
      ? child.material
      : [child.material];
    const clonedMaterials = sourceMaterials.map((sourceMaterial) => {
      const material = sourceMaterial.clone();
      const photoColor =
        photoPaletteByMaterial[sourceMaterial.name] ?? photoPaletteByMaterial[name];
      if (photoColor && material instanceof MeshStandardMaterial)
        material.color.set(photoColor);
      if (material instanceof MeshStandardMaterial)
        material.wireframe = wireframe;
      materials.push(material);
      return material;
    });
    let material: Mesh["material"] = Array.isArray(child.material)
      ? clonedMaterials
      : clonedMaterials[0];
    if (name === "lcd_touch_panel") {
      const display = displayGeometry(geometry);
      geometry.dispose();
      geometry = display;
      material = [clonedMaterials[0], screen];
    }
    const mesh = new Mesh(geometry, material);
    mesh.name = name;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    object.add(mesh);
    geometries.push(geometry);
  });
  if (!object.getObjectByName("lcd_touch_panel"))
    throw new Error("Nido LCD mesh missing");
  return { object, measurement: measureModel(object), materials, geometries };
}
export const meshBounds = (object: Object3D) =>
  new Box3().setFromObject(object);

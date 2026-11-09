import {
  Group,
  Mesh,
  type BufferGeometry,
  type Material,
  type Object3D,
} from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { modelInfo } from "../data/model";

/** Presentation-only batching for this verified static V17, never an articulated rig.
 * Bake existing world transforms into owned copies. Keep the measured LCD separate.
 * Source mesh names, geometry and native GLB remain available to future CAD tooling.
 */
export function batchStaticAssembly(prepared: Object3D) {
  prepared.updateMatrixWorld(true);
  const body: BufferGeometry[] = [];
  const screens: Mesh[] = [];
  const output = new Group();
  const bodyMaterials: Material[] = [];
  const materialIndexes = new Map<string, number>();
  prepared.traverse((child) => {
    if (!(child instanceof Mesh)) return;
    const geometry = child.geometry.clone().applyMatrix4(child.matrixWorld);
    if (child.name === modelInfo.screenMesh) {
      const screen = new Mesh(geometry, child.material);
      screen.name = child.name;
      screens.push(screen);
    } else {
      for (const attribute of Object.keys(geometry.attributes))
        if (!["position", "normal"].includes(attribute))
          geometry.deleteAttribute(attribute);
      const material = Array.isArray(child.material)
        ? child.material[0]
        : child.material;
      const color = "color" in material ? material.color.getHexString() : "";
      const emissive = "emissive" in material
        ? material.emissive.getHexString()
        : "";
      const key = [
        material.type,
        color,
        emissive,
        "roughness" in material ? material.roughness : "",
        "metalness" in material ? material.metalness : "",
        material.map?.uuid ?? "",
      ].join(":");
      let materialIndex = materialIndexes.get(key);
      if (materialIndex === undefined) {
        materialIndex = bodyMaterials.length;
        materialIndexes.set(key, materialIndex);
        bodyMaterials.push(material);
      }
      const indexCount = geometry.index?.count ?? geometry.attributes.position.count;
      geometry.clearGroups();
      geometry.addGroup(0, indexCount, materialIndex);
      body.push(geometry);
    }
  });
  const merged = mergeGeometries(body, true);
  body.forEach((geometry) => geometry.dispose());
  if (!merged || !bodyMaterials.length)
    throw new Error("V17 static geometry could not be batched");
  const mesh = new Mesh(merged, bodyMaterials);
  mesh.name = "V17_static_body";
  output.add(mesh, ...screens);
  return {
    object: output,
    geometries: [merged, ...screens.map((screen) => screen.geometry)],
  };
}

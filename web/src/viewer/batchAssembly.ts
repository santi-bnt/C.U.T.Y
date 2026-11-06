import { Group, Mesh, type BufferGeometry, type Object3D } from "three";
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
  let bodyMaterial: Mesh["material"] | undefined;
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
      body.push(geometry);
      bodyMaterial = child.material;
    }
  });
  const merged = mergeGeometries(body, false);
  body.forEach((geometry) => geometry.dispose());
  if (!merged || !bodyMaterial)
    throw new Error("V17 static geometry could not be batched");
  const mesh = new Mesh(merged, bodyMaterial);
  mesh.name = "V17_static_body";
  output.add(mesh, ...screens);
  return {
    object: output,
    geometries: [merged, ...screens.map((screen) => screen.geometry)],
  };
}

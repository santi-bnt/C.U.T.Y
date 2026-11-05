import {
  Float32BufferAttribute,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  type BufferGeometry,
  type Object3D,
  type Texture,
} from "three";
import { modelInfo } from "../data/model";
import { measureModel } from "./model";

/** Map only the measured front glass triangles. The supplied GLB has no UVs. */
export function displayGeometry(source: BufferGeometry) {
  const geometry = source.clone();
  geometry.computeBoundingBox();
  const box = geometry.boundingBox!;
  const position = geometry.attributes.position;
  const index = geometry.index;
  const count = index?.count ?? position.count;
  const height = box.max.z - box.min.z;
  const width = Math.min(box.max.x - box.min.x, height * 1.5);
  const centerX = (box.max.x + box.min.x) / 2;
  const uv = new Float32Array(position.count * 2);
  for (let vertex = 0; vertex < position.count; vertex++) {
    uv[vertex * 2] = (position.getX(vertex) - centerX) / width + 0.5;
    uv[vertex * 2 + 1] = (position.getZ(vertex) - box.min.z) / height;
  }
  geometry.setAttribute("uv", new Float32BufferAttribute(uv, 2));
  geometry.clearGroups();
  let groupStart = 0;
  let previousMaterial = -1;
  for (let triangle = 0; triangle < count; triangle += 3) {
    const front = [0, 1, 2].every(
      (offset) =>
        Math.abs(
          position.getY(
            index ? index.getX(triangle + offset) : triangle + offset,
          ) - box.min.y,
        ) < 0.001,
    );
    const material = front ? 1 : 0;
    if (material !== previousMaterial) {
      if (previousMaterial !== -1)
        geometry.addGroup(groupStart, triangle - groupStart, previousMaterial);
      groupStart = triangle;
      previousMaterial = material;
    }
  }
  geometry.addGroup(groupStart, count - groupStart, previousMaterial);
  return geometry;
}

export function prepareRobot(
  source: Object3D,
  faceTexture: Texture,
  wireframe: boolean,
) {
  const object = source.clone(true);
  object.rotateX(modelInfo.displayRotationX);
  const body = new MeshStandardMaterial({
    color: "#101114",
    roughness: 0.52,
    metalness: 0.25,
    wireframe,
  });
  const screen = new MeshBasicMaterial({ map: faceTexture, toneMapped: false });
  const geometries: BufferGeometry[] = [];
  let foundDisplay = false;
  object.traverse((child) => {
    if (!(child instanceof Mesh)) return;
    child.castShadow = true;
    child.receiveShadow = true;
    if (child.name === modelInfo.screenMesh) {
      foundDisplay = true;
      child.geometry = displayGeometry(child.geometry);
      geometries.push(child.geometry);
      child.material = [body, screen];
    } else child.material = body;
  });
  if (!foundDisplay)
    throw new Error("The expected V17 LCD glass mesh is missing");
  return {
    object,
    measurement: measureModel(object),
    materials: [body, screen],
    geometries,
  };
}

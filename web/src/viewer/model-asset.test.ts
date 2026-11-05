import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Box3, Mesh, Vector3 } from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { modelInfo } from "../data/model";

describe("deployed original V16 assembly", () => {
  it("contains the expected parts and measures transformed world-space geometry", async () => {
    const bytes = readFileSync("public/models/cuty.glb");
    const gltf = await new GLTFLoader().parseAsync(
      new Uint8Array(bytes).buffer,
      "",
    );
    const size = new Box3()
      .setFromObject(gltf.scene)
      .getSize(new Vector3())
      .multiplyScalar(1000);
    let triangles = 0;
    let meshes = 0;
    gltf.scene.traverse((object) => {
      if (object instanceof Mesh) {
        meshes++;
        triangles +=
          (object.geometry.index?.count ??
            object.geometry.attributes.position.count) / 3;
        expect(object.material).toBeTruthy();
      }
    });
    expect(meshes).toBe(modelInfo.meshes);
    expect(triangles).toBe(modelInfo.triangles);
    size
      .toArray()
      .forEach((value, axis) =>
        expect(value).toBeCloseTo(modelInfo.boundsMm[axis], 2),
      );
    expect(gltf.scene.getObjectByName("Head_Left_V23")).toBeUndefined();
    expect(gltf.scene.getObjectByName("Sombrero_Copa")).toBeUndefined();
    expect(gltf.animations).toHaveLength(0);
  });
});

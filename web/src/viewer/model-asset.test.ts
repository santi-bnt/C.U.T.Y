import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Mesh, MeshBasicMaterial, MeshStandardMaterial, Texture } from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { modelInfo } from "../data/model";
import { prepareRobot } from "./robot";

describe("deployed V17 assembly with integrated display", () => {
  it("contains the expected parts and measures transformed world-space geometry", async () => {
    const bytes = readFileSync("public/models/cuty.glb");
    const gltf = await new GLTFLoader().parseAsync(
      new Uint8Array(bytes).buffer,
      "",
    );
    const texture = new Texture();
    const { object, measurement, materials, geometries } = prepareRobot(
      gltf.scene,
      texture,
      false,
    );
    const size = measurement.size
      .clone()
      .multiplyScalar(modelInfo.millimetersPerUnit);
    let triangles = 0;
    let meshes = 0;
    object.traverse((object) => {
      if (object instanceof Mesh) {
        meshes++;
        triangles +=
          (object.geometry.index?.count ??
            object.geometry.attributes.position.count) / 3;
        expect(object.material).toBeTruthy();
        if (object.name !== modelInfo.screenMesh) {
          expect(
            (object.material as MeshStandardMaterial).color.getHexString(),
          ).toBe("101114");
        }
      }
    });
    expect(meshes).toBe(modelInfo.meshes);
    expect(triangles).toBe(modelInfo.triangles);
    size
      .toArray()
      .forEach((value, axis) =>
        expect(value).toBeCloseTo(modelInfo.boundsMm[axis], 2),
      );
    const display = object.getObjectByName(modelInfo.screenMesh) as Mesh;
    expect((display.material as MeshBasicMaterial[])[1].map).toBe(texture);
    expect(
      display.geometry.groups
        .filter((group) => group.materialIndex === 1)
        .reduce((sum, group) => sum + group.count / 3, 0),
    ).toBe(54);
    expect(display.geometry.attributes.uv.count).toBe(
      display.geometry.attributes.position.count,
    );
    expect(
      (gltf.scene.getObjectByName(modelInfo.screenMesh) as Mesh).geometry
        .attributes.uv,
    ).toBeUndefined();
    expect(gltf.scene.rotation.x).toBe(0);
    expect(gltf.animations).toHaveLength(0);
    materials.forEach((material) => material.dispose());
    geometries.forEach((geometry) => geometry.dispose());
    texture.dispose();
  });
});

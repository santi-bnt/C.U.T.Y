import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  Box3,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  Color,
  Texture,
} from "three";
import { batchStaticAssembly } from "./batchAssembly";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
import { updateAssembly } from "./assembly";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { modelInfo } from "../data/model";
import { photoPaletteByMaterial, prepareRobot } from "./robot";

describe("deployed V17 assembly with integrated display", () => {
  it("batches the static body without changing any triangle or oriented bounds", async () => {
    const bytes = readFileSync("public/models/cuty.glb");
    const gltf = await new GLTFLoader()
      .setMeshoptDecoder(MeshoptDecoder)
      .parseAsync(new Uint8Array(bytes).buffer, "");
    const texture = new Texture();
    const prepared = prepareRobot(gltf.scene, texture, false);
    const before = new Box3().setFromObject(prepared.object);
    const batched = batchStaticAssembly(prepared.object);
    const after = new Box3().setFromObject(batched.object);
    let meshes = 0,
      triangles = 0;
    batched.object.traverse((object) => {
      if (object instanceof Mesh) {
        meshes++;
        triangles +=
          (object.geometry.index?.count ??
            object.geometry.attributes.position.count) / 3;
      }
    });
    expect(meshes).toBe(2);
    expect(triangles).toBe(modelInfo.triangles);
    before.min
      .toArray()
      .forEach((value, i) =>
        expect(after.min.toArray()[i]).toBeCloseTo(value, 3),
      );
    before.max
      .toArray()
      .forEach((value, i) =>
        expect(after.max.toArray()[i]).toBeCloseTo(value, 3),
      );
    expect(batched.object.getObjectByName(modelInfo.screenMesh)).toBeTruthy();
    const arm = prepared.object.getObjectByName("A2_Arm_R")!;
    const head = prepared.object.getObjectByName("H1_Head_Front")!;
    updateAssembly(prepared.object, "assembled", "wave", 1);
    expect(Math.abs(arm.rotation.x)).toBeGreaterThan(0.5);
    updateAssembly(prepared.object, "assembled", "look", 1);
    expect(Math.abs(head.rotation.y)).toBeGreaterThan(0.1);
    updateAssembly(prepared.object, "exploded", "none", 0);
    expect(head.position.length()).toBeGreaterThan(30);
    updateAssembly(prepared.object, "interior", "none", 0);
    expect(head.visible).toBe(false);
    updateAssembly(prepared.object, "assembled", "none", 0);
    expect(head.visible).toBe(true);
    expect(head.position.length()).toBe(0);

    [...prepared.geometries, ...batched.geometries].forEach((geometry) =>
      geometry.dispose(),
    );
    prepared.materials.forEach((material) => material.dispose());
    texture.dispose();
  });
  it("contains the expected parts and measures transformed world-space geometry", async () => {
    const bytes = readFileSync("public/models/cuty.glb");
    const gltf = await new GLTFLoader()
      .setMeshoptDecoder(MeshoptDecoder)
      .parseAsync(new Uint8Array(bytes).buffer, "");
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
    let photoMatchedMaterials = 0;
    const authoredColors = new Set<string>();
    object.traverse((object) => {
      if (object instanceof Mesh) {
        meshes++;
        triangles +=
          (object.geometry.index?.count ??
            object.geometry.attributes.position.count) / 3;
        expect(object.material).toBeTruthy();
        const sourceNode = gltf.scene.getObjectByName(object.name);
        const sourceMesh = (sourceNode?.getObjectByProperty(
          "isMesh",
          true,
        ) ?? sourceNode) as Mesh | undefined;
        expect(sourceMesh).toBeTruthy();
        const sourceMaterial = Array.isArray(sourceMesh!.material)
          ? sourceMesh!.material[0]
          : sourceMesh!.material;
        const displayedMaterial = Array.isArray(object.material)
          ? object.material[0]
          : object.material;
        const expectedColor = photoPaletteByMaterial[sourceMaterial.name];
        if (expectedColor) photoMatchedMaterials++;
        expect(
          (displayedMaterial as MeshStandardMaterial).color.getHexString(),
        ).toBe(
          expectedColor
            ? new Color(expectedColor).getHexString()
            : (sourceMaterial as MeshStandardMaterial).color.getHexString(),
        );
        authoredColors.add(
          (displayedMaterial as MeshStandardMaterial).color.getHexString(),
        );
      }
    });
    // GLTFLoader converts authored sRGB factors into Three.js working space;
    // assert a varied preserved palette rather than comparing encoded hex.
    expect(authoredColors.size).toBeGreaterThan(3);
    expect(photoMatchedMaterials).toBeGreaterThan(0);
    expect(meshes).toBe(modelInfo.meshes);
    expect(triangles).toBe(modelInfo.triangles);
    size
      .toArray()
      .forEach((value, axis) =>
        expect(value).toBeCloseTo(modelInfo.boundsMm[axis], 2),
      );
    const display = object.getObjectByName(modelInfo.screenMesh) as Mesh;
    expect((display.material as MeshBasicMaterial[])[1].map).toBe(texture);
    const lcdTriangles = display.geometry.groups
        .filter((group) => group.materialIndex === 1)
        .reduce((sum, group) => sum + group.count / 3, 0);
    expect(lcdTriangles).toBeGreaterThan(0);
    expect(display.geometry.attributes.uv.count).toBe(
      display.geometry.attributes.position.count,
    );
    expect(
      (
        gltf.scene
          .getObjectByName(modelInfo.screenMesh)!
          .getObjectByProperty("isMesh", true) as Mesh
      ).geometry.attributes.uv,
    ).toBeUndefined();
    expect(gltf.scene.rotation.x).toBe(0);
    expect(gltf.animations).toHaveLength(0);
    materials.forEach((material) => material.dispose());
    geometries.forEach((geometry) => geometry.dispose());
    texture.dispose();
  });
});

import { Buffer } from "node:buffer";
import { log } from "node:console";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { GLTFExporter } from "three/examples/jsm/exporters/GLTFExporter.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
import { Box3, Group, Mesh, Vector3 } from "three";

class BlobReader {
  readAsArrayBuffer(blob) {
    blob.arrayBuffer().then((result) => {
      this.result = result;
      this.onloadend?.();
    });
  }

  readAsDataURL(blob) {
    blob.arrayBuffer().then((result) => {
      this.result = `data:${blob.type};base64,${Buffer.from(result).toString("base64")}`;
      this.onloadend?.();
    });
  }
}

globalThis.FileReader = BlobReader;

const nativePath = "node_modules/.cache/cadquery-builder/out/cuty_v17_web.glb";
const optimizedPath = "node_modules/.cache/cadquery-builder/cuty-v17-web-optimized.glb";
const outputPath = "public/models/cuty.glb";
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const load = async (path) =>
  loader.parseAsync(new Uint8Array(readFileSync(path)).buffer, "");
const native = await load(nativePath);
const web = await load(optimizedPath);
native.scene.updateMatrixWorld(true);
web.scene.updateMatrixWorld(true);

const requiredParts = ["H3_Visor", "H4_Display_Bars", "S3_Tummy_Grille", "lcd_touch_panel"];
const partMeshes = [];
native.scene.traverse((object) => {
  if (object instanceof Mesh && object.name) partMeshes.push(object);
});
const partsByName = new Map(partMeshes.map((mesh) => [mesh.name, mesh]));
for (const name of requiredParts) {
  if (!partsByName.has(name)) throw new Error(`Current Nido model is missing ${name}`);
}

const bounds = new Box3().setFromObject(web.scene);
const boundsMm = bounds.getSize(new Vector3()).toArray();
const parts = partMeshes.map((mesh) => {
  const box = new Box3().setFromObject(mesh);
  return {
    name: mesh.name,
    size: box.getSize(new Vector3()).toArray(),
    center: box.getCenter(new Vector3()).toArray(),
  };
});
const partRecord = (name) => parts.find((part) => part.name === name);
const visorDepth = Math.min(...partRecord("H3_Visor").size);
const barDimensions = [...partRecord("H4_Display_Bars").size].sort((a, b) => a - b);
if (Math.abs(visorDepth - 10.72) > 0.2 || barDimensions[2] < 86.5) {
  throw new Error("Current visor or camera-bar revision failed its geometry checks");
}
if (boundsMm.some((value) => !Number.isFinite(value))) {
  throw new Error("Invalid current Nido model bounds");
}

let triangles = 0;
web.scene.traverse((object) => {
  if (object instanceof Mesh) {
    triangles += (object.geometry.index?.count ?? object.geometry.attributes.position.count) / 3;
  }
});

const carrier = new Group();
carrier.name = "Nido_carrier_mechanical_reference";
native.scene.traverse((object) => {
  if (!(object instanceof Mesh) || !/^(pcb_|respeaker_|fuse_)/.test(object.name)) return;
  const mesh = object.clone();
  mesh.geometry = object.geometry.clone().applyMatrix4(object.matrixWorld);
  mesh.position.set(0, 0, 0);
  mesh.rotation.set(0, 0, 0);
  mesh.scale.set(1, 1, 1);
  carrier.add(mesh);
});
if (!carrier.children.length) throw new Error("Current model contains no carrier reference meshes");
const carrierCenter = new Box3().setFromObject(carrier).getCenter(new Vector3());
carrier.children.forEach((mesh) => mesh.geometry.translate(-carrierCenter.x, -carrierCenter.y, -carrierCenter.z));
const carrierGlb = await new GLTFExporter().parseAsync(carrier, {
  binary: true,
  onlyVisible: false,
});
writeFileSync("public/models/carrier-assembly.glb", Buffer.from(carrierGlb));
writeFileSync(outputPath, readFileSync(optimizedPath));

const nativeHash = createHash("sha256").update(readFileSync(nativePath)).digest("hex");
const webBytes = readFileSync(outputPath);
const manifestPath = "public/assembly/provenance.json";
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
manifest.geometrySource =
  "hardware/cad/carcasa_v17/fuente_cad/v17/build.py + web/scripts/data/cadquery/parts.json";
manifest.currentModelBuild = {
  revision: "V17 Nido - 2026-11-06",
  nativeGlb: "node_modules/.cache/cadquery-builder/out/cuty_v17_web.glb",
  nativeGlbSha256: nativeHash,
  cadqueryTessellation: "tol=0.25 mm, angularTolerance=0.17 rad",
  optimization: "gltfpack -kn -km -vp 16 -vn 12 -cc; no simplification requested",
  verifiedGeometry: {
    visorDepthMm: visorDepth,
    displayBarHeightMm: barDimensions[2],
    lcdMesh: "lcd_touch_panel",
  },
};
manifest.webGlbRevision = "V17 Nido - 2026-11-06";
manifest.webGlbPrintCadNote =
  "The interactive model is rebuilt from the November 6 CadQuery revision. The optimized mesh preserves the updated camera cradle, three display/camera bars, and LCD component.";
manifest.sourceGlbSha256 = nativeHash;
manifest.sourcePackageGlbSha256 = "0d604e5edfaa8332aa2df40562cf05b2d06728c236c5cabd6ec9095d132b12d1";
manifest.webGlbSha256 = createHash("sha256").update(webBytes).digest("hex");
manifest.webGlbBytes = webBytes.length;
writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

const metadata = {
  revision: "V17 Nido - 2026-11-06",
  triangles,
  meshes: parts.length,
  boundsMm,
  parts,
  pcb: {
    model: "models/carrier-assembly.glb",
    meshes: carrier.children.length,
    simplified: true,
    source: "CUTY_V17_Nido_rev.zip / fuente_cad/v17/refs.py",
    missingRefs: ["H1", "H2", "H3", "H4", "NT1"],
    revisionDifferences: ["F1/F2 pad Y differs from native KiCad by 3.4 mm"],
  },
};
writeFileSync("src/data/nido.generated.json", `${JSON.stringify(metadata, null, 2)}\n`);
log(
  JSON.stringify({
    revision: metadata.revision,
    triangles,
    meshes: parts.length,
    boundsMm: boundsMm.map((value) => +value.toFixed(2)),
    visorDepthMm: +visorDepth.toFixed(2),
    displayBarHeightMm: +barDimensions[2].toFixed(2),
    carrierMeshes: carrier.children.length,
    webGlbBytes: webBytes.length,
  }),
);

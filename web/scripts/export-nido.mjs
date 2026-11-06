import { Buffer } from "node:buffer";
import { console } from "node:console";
/** Export mechanical PCB reference from the supplied revised CAD, never fabricate geometry. */
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
      this.result =
        "data:" +
        blob.type +
        ";base64," +
        Buffer.from(result).toString("base64");
      this.onloadend?.();
    });
  }
}
globalThis.FileReader = BlobReader;
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const load = async (path) =>
  await loader.parseAsync(new Uint8Array(readFileSync(path)).buffer, "");
const revised = await load(
  "node_modules/.cache/cuty-nido-revision/CUTY_V17_Nido/CUTY_V17.glb",
);
revised.scene.updateMatrixWorld(true);
const pcb = new Group();
pcb.name = "Nido_carrier_mechanical_reference";
revised.scene.traverse((child) => {
  if (child instanceof Mesh && /^(pcb_|respeaker_|fuse_)/.test(child.name)) {
    const mesh = child.clone();
    mesh.geometry = child.geometry.clone().applyMatrix4(child.matrixWorld);
    mesh.position.set(0, 0, 0);
    mesh.rotation.set(0, 0, 0);
    mesh.scale.set(1, 1, 1);
    pcb.add(mesh);
  }
});
const pcbCenter = new Box3().setFromObject(pcb).getCenter(new Vector3());
pcb.children.forEach((mesh) =>
  mesh.geometry.translate(-pcbCenter.x, -pcbCenter.y, -pcbCenter.z),
);
const output = await new GLTFExporter().parseAsync(pcb, {
  binary: true,
  onlyVisible: false,
});
writeFileSync("public/models/carrier-assembly.glb", Buffer.from(output));
const web = await load("public/models/cuty.glb");
web.scene.updateMatrixWorld(true);
const parts = [];
let triangles = 0;
web.scene.traverse((obj) => {
  if (obj instanceof Mesh)
    triangles +=
      (obj.geometry.index?.count ?? obj.geometry.attributes.position.count) / 3;
  if (obj.name && revised.scene.getObjectByName(obj.name)) {
    const box = new Box3().setFromObject(obj);
    parts.push({
      name: obj.name,
      size: box.getSize(new Vector3()).toArray(),
      center: box.getCenter(new Vector3()).toArray(),
    });
  }
});
const metadata = {
  revision: "V17 Nido · 2026-11-05",
  triangles,
  meshes: revised.scene.children.length,
  boundsMm: new Box3()
    .setFromObject(web.scene)
    .getSize(new Vector3())
    .toArray(),
  parts,
  pcb: {
    model: "models/carrier-assembly.glb",
    meshes: pcb.children.length,
    simplified: true,
    source: "CUTY_V17_Nido_rev.zip / fuente_cad/v17/refs.py",
    missingRefs: ["H1", "H2", "H3", "H4", "NT1"],
    revisionDifferences: ["F1/F2 pad Y differs from native KiCad by 3.4 mm"],
  },
};
writeFileSync(
  "src/data/nido.generated.json",
  JSON.stringify(metadata, null, 2),
);
console.log(
  JSON.stringify({
    triangles,
    meshes: metadata.meshes,
    bounds: metadata.boundsMm,
    pcbMeshes: pcb.children.length,
    pcbBytes: output.byteLength,
  }),
);

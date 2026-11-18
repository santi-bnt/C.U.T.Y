// Build from original STL buffers + rigid node transforms. No CadQuery rebuild,
// mesh repair, welding, simplification, quantization or dimensional scaling.
import { Buffer } from "node:buffer";
import { log } from "node:console";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Box3, Group, Matrix4, Mesh, MeshStandardMaterial, Vector3, Float32BufferAttribute } from "three";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { GLTFExporter } from "three/examples/jsm/exporters/GLTFExporter.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const path = (p) => resolve(root, p);
const json = (p) => JSON.parse(readFileSync(path(p), "utf8"));
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const selection = json("hardware/cad/carcasa_v17_fija/stl-selection.json");
const historical = json("hardware/cad/glb/archive/CUTY_V17_Nido_20261106_metadata.json");
const oldParts = new Map(historical.parts.map(p => [p.name, p]));
const sourceDir = "hardware/cad/carcasa_v17_fija/STL_imprimir";
const out = "web/public/assembly";
mkdirSync(path(out), { recursive: true });
class BlobReader {
  readAsArrayBuffer(blob) { blob.arrayBuffer().then(result => { this.result=result; this.onloadend?.(); }); }
  readAsDataURL(blob) { blob.arrayBuffer().then(result => { this.result=`data:${blob.type};base64,${Buffer.from(result).toString("base64")}`; this.onloadend?.(); }); }
}
globalThis.FileReader = BlobReader;
const arrayBuffer = bytes => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset+bytes.byteLength);
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const referencePath = "hardware/cad/glb/archive/CUTY_V17_Nido_20261106_web.glb";
const reference = await loader.parseAsync(arrayBuffer(readFileSync(path(referencePath))), "");
reference.scene.updateMatrixWorld(true);
const assembly = new Group(); assembly.name="CUTY_V17_Fixed_Three_Joints";
// Invert export.py's print rotations (about the origin; translation is restored
// from CAD reference datums below), then map Z-up CAD to the existing Y-up viewer.
const orientations = {
  B1_Pedestal:["x",180], K2_Core_Spine:["x",-90], K3_Core_Shoulders:["x",180],
  K5_Power_Rack:["x",-90], S1_Body_Front_Fixed:["x",-90], S2_Body_Back_Fixed:["x",90],
  S3_Tummy_Grille:["x",-90], S4_USB_Plug:["y",-90],
  H1_Head_Front:["x",-90], H2_Head_Back:["x",90], H3_Visor:["x",90], H4_Display_Bars:["x",90],
  A1_Arm_L:["y",-90], A2_Arm_R:["y",90], A3_Hand_L:["y",-90], A4_Hand_R:["y",90],
  A5_Arm_Cap_L:["y",-90], A6_Arm_Cap_R:["y",90], H6_Ear_L:["y",-90], H7_Ear_R:["y",90],
};
const axis = { x:new Vector3(1,0,0), y:new Vector3(0,1,0) };
const ground = 48.7; // pedestal.py: PED_TOP(82.7) - PED_H(34.0).
const yup = new Matrix4().makeRotationX(-Math.PI/2);
const records=[];
function material(name) {
  const color = /^H3_/.test(name) ? "#171717" :
    /^(S[12]_|A[12]_|H[12]_)/.test(name) ? "#f4f2ee" :
    /^(B1_|B3_)/.test(name) ? "#dfc09a" :
    /^(S[34]_|A[3-6]_|H[6-8]_)/.test(name) ? "#ff6a00" : "#888a88";
  const m=new MeshStandardMaterial({color,roughness:0.55}); m.name=name; return m;
}
for (const part of selection.parts) {
  const bytes=readFileSync(path(`${sourceDir}/${part.file}`));
  if(hash(bytes)!==part.sha256) throw new Error(`STL changed before build: ${part.file}`);
  const geometry=new STLLoader().parse(arrayBuffer(bytes));
  const [a,deg]=orientations[part.name]??["x",0];
  const inverse=new Matrix4().makeRotationAxis(axis[a],-deg*Math.PI/180);
  // Bounding boxes are measured on the actual vertices, not rotated AABB corners.
  const unrotated=new Box3(); const v=new Vector3();
  const positions=geometry.attributes.position;
  for(let i=0;i<positions.count;i++) unrotated.expandByPoint(v.fromBufferAttribute(positions,i).applyMatrix4(inverse));
  const center=unrotated.getCenter(new Vector3()); const t=new Vector3();
  const prior=oldParts.get(part.name);
  let datum="Existing source CAD placement, shared with fixed variant";
  if(prior) t.set(prior.center[0]-center.x,-prior.center[2]-center.y,prior.center[1]-center.z);
  // Datum planes from pedestal.py, common.py, head.py and shells.py. Preserve
  // real vertex coordinates; only rotation and translation are applied.
  if(part.name==="B1_Pedestal") { t.set(-center.x,63-unrotated.max.y,ground-unrotated.min.z); datum="Pedestal: table z=GROUND; back radial extreme y=63"; }
  if(part.name==="B2_Pedestal_Floor") { t.set(-center.x,-center.y,ground-unrotated.min.z); datum="Pedestal floor on table, common Z axis"; }
  if(part.name==="B3_Pedestal_Drawer") { t.set(-center.x,63-unrotated.max.y,ground+3.2-unrotated.min.z); datum="Drawer face y=63, tray bottom z=GROUND+3.2"; }
  if(part.name==="B4_Deck_Riser") { t.set(-center.x,-center.y,82.7-unrotated.min.z); datum="Riser bottom at PED_TOP=82.7"; }
  if(part.name==="K1_Core_Deck_Fixed") { t.set(-center.x,-center.y,97-unrotated.min.z); datum="Fixed deck at DECK_Z0=97, common XY axis"; }
  if(part.name==="S1_Body_Front_Fixed") { t.set(-center.x,6-unrotated.max.y,83-unrotated.min.z); datum="Front shell seam y=ARM_AXIS_Y=6, bottom z=PED_CUT=83"; }
  if(part.name==="S2_Body_Back_Fixed") { t.set(-center.x,6-unrotated.min.y,83-unrotated.min.z); datum="Rear shell seam y=6, bottom z=83"; }
  if(part.name==="H1_Head_Front") { t.set(-center.x,4-unrotated.max.y,205.5-unrotated.min.z); datum="Head front seam y=HEAD_YC=4, neck bottom z=205.5"; }
  if(part.name==="H2_Head_Back") { t.set(-center.x,4-unrotated.min.y,205.5-unrotated.min.z); datum="Head back seam y=4, neck bottom z=205.5"; }
  if(part.name==="S3_Tummy_Grille") { t.set(-center.x,-57.4-unrotated.max.y,114-center.z); datum="Grille flat rear y=SPEAKER_FRONT+thickness-1=-57.4, z=114"; }
  if(!prior && !datum.startsWith("Pedestal") && !/^(B[34]_|K1_|S[12]_)/.test(part.name)) throw new Error(`Missing placement: ${part.name}`);
  t.z-=ground;
  const matrix=yup.clone().multiply(new Matrix4().makeTranslation(...t.toArray())).multiply(inverse);
  if(Math.abs(matrix.determinant()-1)>1e-9) throw new Error("Non-rigid STL transform");
  const mesh=new Mesh(geometry,material(part.name)); mesh.name=part.name;
  mesh.matrixAutoUpdate=false; mesh.matrix.copy(matrix); mesh.matrix.decompose(mesh.position,mesh.quaternion,mesh.scale);
  mesh.userData={sourceStl:`${sourceDir}/${part.file}`,sha256:part.sha256,rigidOnly:true};
  assembly.add(mesh);
  const printBounds = new Box3().setFromBufferAttribute(positions);
  records.push({...part,triangles:positions.count/3,printBoundsMm:[printBounds.min.toArray(),printBounds.max.toArray()],
    cadBoundsAfterUnrotation:[unrotated.min.toArray(),unrotated.max.toArray()],matrix:matrix.toArray(),datum});
}
// Purchased reference envelopes are retained from the historical assembly,
// without re-tessellating the PCB. Its separate 45-part GLB stays byte-identical.
const omitted=[];
reference.scene.traverse(object=>{
  if(!(object instanceof Mesh)) return;
  let parent=object; while(parent && !oldParts.has(parent.name)) parent=parent.parent;
  const name=parent?.name??object.name;
  if(/^[ABGHKS]\d_/.test(name)) return;
  if(/^(servo_gimbal_|pushrod_|bolt_roll|bolt_pitch|screw_crank_|battery_lead)/.test(name)) { omitted.push(name); return; }
  const geometry=object.geometry.clone();
  for(const key of ["position","normal"]) {
    const attribute=geometry.getAttribute(key); if(!attribute) continue;
    const values=new Float32Array(attribute.count*3);
    for(let i=0;i<attribute.count;i++) { values[3*i]=attribute.getX(i);values[3*i+1]=attribute.getY(i);values[3*i+2]=attribute.getZ(i); }
    geometry.setAttribute(key,new Float32BufferAttribute(values,3));
  }
  geometry.applyMatrix4(object.matrixWorld);
  const mesh=new Mesh(geometry,object.material); mesh.name=name;
  let matrix=new Matrix4().makeTranslation(0,-ground,0);
  if(name==="battery_3s_2200") {
    const cy=Math.sqrt(59.5**2-17.5**2)-0.25-54;
    const c=oldParts.get(name).center;
    matrix=new Matrix4().makeTranslation(0,17.3,-cy)
      .multiply(new Matrix4().makeRotationY(Math.PI/2)).multiply(new Matrix4().makeTranslation(-c[0],-c[1],-c[2]));
  }
  if(name==="switch_main"||name==="switch_servos") {
    const left=name==="switch_main", angle=(left?166:14)*Math.PI/180;
    const origin=[86*Math.cos(angle),22,-86*Math.sin(angle)];
    matrix=new Matrix4().makeTranslation(left?-63:63,18,0)
      .multiply(new Matrix4().makeRotationY((left?14:-14)*Math.PI/180))
      .multiply(new Matrix4().makeTranslation(-origin[0],-origin[1],-origin[2]));
  }
  mesh.matrixAutoUpdate=false; mesh.matrix.copy(matrix); mesh.matrix.decompose(mesh.position,mesh.quaternion,mesh.scale);
  assembly.add(mesh);
});
assembly.updateMatrixWorld(true);
const names=assembly.children.map(x=>x.name);
if(new Set(names).size!==names.length || records.length!==27) throw new Error("Duplicate or missing printed component");
if(names.filter(n=>/^servo_.*_case$/.test(n)).length!==3) throw new Error("Expected exactly three servo reference cases");
const pivots={
  HEAD_PAN:{point:[0,166.3,0],axis:[0,1,0],source:"refs.py SERVO_FRAMES.servo_head; pedestal.GROUND"},
  LEFT_ARM:{point:[-63,127.3,-6],axis:[1,0,0],source:"refs.py ARM_SERVO_TOP_X; common.py ARM_AXIS_Z/Y; pedestal.GROUND"},
  RIGHT_ARM:{point:[63,127.3,-6],axis:[1,0,0],source:"same CAD shoulder-shaft datums"},
};
const outputPath="web/public/models/cuty.glb";
const glb=Buffer.from(await new GLTFExporter().parseAsync(assembly,{binary:true,onlyVisible:false}));
writeFileSync(path(outputPath),glb);
// Verify exported positions equal the STL buffer exactly, in original print
// coordinates. Matrices, not rewritten vertices, place every printed component.
const verified=await loader.parseAsync(arrayBuffer(glb),"");
verified.scene.updateMatrixWorld(true);
const parts=[]; let triangles=0;
verified.scene.traverse(m=>{
  if(!(m instanceof Mesh)) return;
  const name=m.userData.sourceStl?m.name:(()=>{let p=m;while(p&&!names.includes(p.name))p=p.parent;return p?.name??m.name;})();
  const bounds=new Box3().setFromObject(m);
  parts.push({name,size:bounds.getSize(new Vector3()).toArray(),center:bounds.getCenter(new Vector3()).toArray()});
  triangles+=(m.geometry.index?.count??m.geometry.attributes.position.count)/3;
  const row=records.find(p=>p.name===name);
  if(row) {
    const src=assembly.getObjectByName(name).geometry.attributes.position;
    const dst=m.geometry.attributes.position;
    if(src.count!==dst.count) throw new Error(`Triangle count changed: ${name}`);
    for(let i=0;i<src.count;i++) for(const method of ["getX","getY","getZ"])
      if(src[method](i)!==dst[method](i)) throw new Error(`Vertex changed: ${name}/${i}`);
    row.exportedPositionsExact=true;
  }
});
if(records.some(p=>!p.exportedPositionsExact)) throw new Error("STL absent from exported GLB");
const boundsMm=new Box3().setFromObject(verified.scene).getSize(new Vector3()).toArray();
if(Math.abs(boundsMm[1]-316.3)>0.15) throw new Error(`Unexpected fixed height: ${boundsMm[1]}`);
for(const row of records) if(hash(readFileSync(path(`${sourceDir}/${row.file}`)))!==row.sha256) throw new Error("STL changed after export");
const revision="V17 Fijo STL / 2026-11-13";
const metadata={revision,triangles,meshes:parts.length,boundsMm,parts,pcb:historical.pcb,pivots,
  sourceStlParts:27,activeJoints:["HEAD_PAN","LEFT_ARM","RIGHT_ARM"],reservedConnectors:["J10","J11"]};
writeFileSync(path("web/src/data/nido.generated.json"),JSON.stringify(metadata,null,2)+"\n");
const manifest={revision,auditedOn:selection.auditedOn,sourceDirectory:sourceDir,webGlbSha256:hash(glb),webGlbBytes:glb.length,
  sourceReference:{path:referencePath,sha256:hash(readFileSync(path(referencePath))),scope:"Historical purchased envelopes only; not printed geometry"},
  geometryPolicy:"Original STL positions and triangle order exported exactly. Rigid node matrices only. No repair, remeshing, quantization or structural scaling.",
  printed:records,pivots,omittedHistoricalReferences:omitted,
  omittedNewPurchasedReferences:["8 pedestal/deck screws","battery lead envelope","XT60 joint envelope"],
  validation:"27 printed parts and 3 servo cases; exact local vertices and source SHA-256 checked. Datum alignment and bounding dimensions checked, not exact collision or physical fit validation."};
writeFileSync(path(`${out}/fixed-stl-manifest.json`),JSON.stringify(manifest,null,2)+"\n");
const provenance=json("web/public/assembly/provenance.json");
provenance.historicalModelBuild ??= provenance.currentModelBuild;
provenance.currentModelBuild=manifest;
provenance.geometrySource=sourceDir;
provenance.webGlbRevision=revision; provenance.webGlbSha256=hash(glb);provenance.webGlbBytes=glb.length;
provenance.webGlbPrintCadNote="Current fixed STL meshes, rigidly assembled; historical purchased electronics are simplified references. Physical fit and motion remain unvalidated.";
writeFileSync(path(`${out}/provenance.json`),JSON.stringify(provenance,null,2)+"\n");
log(JSON.stringify({revision,stls:records.length,meshes:parts.length,triangles,boundsMm,bytes:glb.length,sha256:hash(glb)}));

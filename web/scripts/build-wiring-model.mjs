import { readFileSync, writeFileSync } from "node:fs";
import { Buffer } from "node:buffer";
import { Group, Mesh } from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { GLTFExporter } from "three/examples/jsm/exporters/GLTFExporter.js";
class BlobReader {
  readAsArrayBuffer(blob) { blob.arrayBuffer().then(result => { this.result=result; this.onloadend?.(); }); }
  readAsDataURL(blob) { blob.arrayBuffer().then(result => { this.result=`data:${blob.type};base64,${Buffer.from(result).toString("base64")}`; this.onloadend?.(); }); }
}
globalThis.FileReader=BlobReader;
const input=readFileSync("public/models/cuty.glb");
const model=await new GLTFLoader().parseAsync(input.buffer.slice(input.byteOffset,input.byteOffset+input.byteLength),"");
model.scene.updateMatrixWorld(true);
const group=new Group(); group.name="Fixed_Wiring_Interior";
const keep=/^(K[1-5]_|B[24]_|H[45]_|pcb_|respeaker_|fuse_|pi5_|lcd_|camera_|servo_|battery_|buck_|reg_5v1_usbc|switch_|speaker_|imu_)/;
model.scene.traverse(object=>{
  if(!(object instanceof Mesh)) return;
  let node=object; while(node.parent&&!keep.test(node.name)) node=node.parent;
  const name=node.name;
  if(!keep.test(name)) return;
  const mesh=new Mesh(object.geometry,object.material); mesh.name=name;
  mesh.matrixAutoUpdate=false; mesh.matrix.copy(object.matrixWorld);
  mesh.matrix.decompose(mesh.position,mesh.quaternion,mesh.scale); group.add(mesh);
});
if(!group.getObjectByName("lcd_touch_panel")||!group.getObjectByName("servo_head_case")) throw new Error("Required interior components missing");
const bytes=await new GLTFExporter().parseAsync(group,{binary:true});
writeFileSync("public/models/wiring-interior.glb",Buffer.from(bytes));

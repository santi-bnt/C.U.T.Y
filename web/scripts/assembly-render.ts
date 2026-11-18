import { AmbientLight, CanvasTexture, Color, DirectionalLight, ImageLoader, Mesh, OrthographicCamera, Scene, SRGBColorSpace, Vector3, WebGLRenderer } from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
import { prepareRobot } from "../src/viewer/robot";
const gltf=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync("/models/cuty.glb");
const atlas=await new ImageLoader().loadAsync("/face/idle.webp");
const face=document.createElement("canvas"); face.width=480;face.height=320;
face.getContext("2d")!.drawImage(atlas,0,0,480,320,0,0,480,320);
const texture=new CanvasTexture(face); texture.colorSpace=SRGBColorSpace;
const prepared=prepareRobot(gltf.scene,texture,false);
const scene=new Scene();
scene.add(prepared.object,new AmbientLight(0xffffff,2));
const sun=new DirectionalLight(0xffffff,3); sun.position.set(280,480,500);scene.add(sun);
const fill=new DirectionalLight(new Color("#ff9b5c"),0.7);fill.position.set(-250,150,-250);scene.add(fill);
const renderer=new WebGLRenderer({alpha:true,antialias:true,preserveDrawingBuffer:true});
renderer.setSize(1050,930); renderer.setPixelRatio(1); renderer.setClearColor(0x000000,0);
document.body.appendChild(renderer.domElement);
const camera=new OrthographicCamera(-210,210,186,-186,1,2500);
camera.position.set(410,310,670); camera.lookAt(new Vector3(0,155,0));
const stagePatterns=[
  /.*/,
  /^[ABHKS]\d_/,
  /^B2_/,
  /^B[12]_/,
  /^B[123]_/,
  /^B[1-4]_/,
  /^(B[1-4]_|K1_)/,
  /^(B[1-4]_|K[12]_)/,
  /^(B[1-4]_|K[12]_|pcb_|fuse_|respeaker_)/,
  /^(B[1-4]_|K[12]_|pcb_|fuse_|respeaker_|pi5_)/,
  /^(B[1-4]_|K[125]_|pcb_|fuse_|respeaker_|pi5_|buck_|reg_)/,
  /^(B[1-4]_|K[1-5]_|pcb_|fuse_|respeaker_|pi5_|buck_|reg_|servo_arm_)/,
  /^(B[1-4]_|K[1-5]_|H[34]_|lcd_|camera_|pcb_|fuse_|respeaker_|pi5_|buck_|reg_|servo_)/,
  /^(B[1-4]_|K[1-5]_|H[1-8]_|lcd_|camera_|pcb_|fuse_|respeaker_|pi5_|buck_|reg_|servo_)/,
  /^(B[1-4]_|K[1-5]_|H[1-8]_|S[1-4]_|lcd_|camera_|pcb_|fuse_|respeaker_|pi5_|buck_|reg_|servo_)/,
  /^(B[1-4]_|K[1-5]_|H[1-8]_|S[1-4]_|A[1-6]_|lcd_|camera_|pcb_|fuse_|respeaker_|pi5_|buck_|reg_|servo_)/,
  /.*/,
  /.*/,
];
declare global { interface Window { renderAssemblyStage: (stage:number)=>void } }
window.renderAssemblyStage=(stage:number)=>{
  const pattern=stagePatterns[stage];
  prepared.object.traverse(child=>{if(child instanceof Mesh) child.visible=pattern.test(child.name);});
  renderer.render(scene,camera);
};
window.renderAssemblyStage(0);
document.body.dataset.ready="true";

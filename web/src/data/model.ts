import nido from "./nido.generated.json";
export const modelInfo = {
  revision: nido.revision,
  url: `${import.meta.env.BASE_URL}models/cuty.glb?v=nido-rev-20261106`,
  triangles: nido.triangles,
  meshes: nido.meshes,
  boundsMm: nido.boundsMm,
  millimetersPerUnit: 1,
  displayRotationX: 0,
  screenMesh: "lcd_touch_panel",
};

// Start Vite first; render 18 illustrative stills from the current GLB.
/* global document, window */
import { chromium } from "@playwright/test";
import { writeFileSync } from "node:fs";
import { Buffer } from "node:buffer";
import { spawnSync } from "node:child_process";
import process from "node:process";
const base=process.env.CUTY_RENDER_URL || "http://127.0.0.1:5188";
const executablePath=process.env.CUTY_BROWSER_PATH || (process.platform==="win32" ? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" : undefined);
const browser=await chromium.launch({executablePath,args:["--enable-unsafe-swiftshader"]});
try {
  const page=await browser.newPage({viewport:{width:1050,height:930},deviceScaleFactor:1});
  page.on("pageerror",error=>process.stderr.write(error.stack+"\n"));
  await page.goto(base+"/scripts/assembly-render.html");
  await page.waitForFunction(()=>document.body.dataset.ready==="true",{timeout:60000});
  const stages=process.env.CUTY_STAGES ? process.env.CUTY_STAGES.split(",").map(Number) : Array.from({length:18},(_,i)=>i+1);
  if(stages.some(stage=>!Number.isInteger(stage)||stage<1||stage>18)) throw new Error("CUTY_STAGES must contain stage numbers 1–18");
  for(const stage of stages) {
    const data=await page.evaluate(stage=>{
      window.renderAssemblyStage(stage);
      return document.querySelector("canvas").toDataURL("image/webp",0.92).split(",")[1];
    },stage-1);
    writeFileSync(`public/assembly/fixed-${String(stage).padStart(2,"0")}.webp`,Buffer.from(data,"base64"));
    if(stage===16||stage===17) {
      writeFileSync(`public/assembly/fixed-${stage}-still.webp`,Buffer.from(data,"base64"));
      const frames=[];
      for(let i=0;i<20;i++) {
        const progress=(1-Math.cos(2*Math.PI*i/20))/2;
        const frame=await page.evaluate(({stage,progress})=>{
          window.renderAssemblyStage(stage-1,progress);
          return document.querySelector("canvas").toDataURL("image/webp",0.9).split(",")[1];
        },{stage,progress});
        frames.push(frame);
      }
      const encoder="import base64,io,json,sys\nfrom PIL import Image\na=[Image.open(io.BytesIO(base64.b64decode(x))).convert('RGBA') for x in json.load(sys.stdin)]\nb=io.BytesIO(); a[0].save(b,format='WEBP',save_all=True,append_images=a[1:],duration=110,loop=0,quality=88,method=4); sys.stdout.buffer.write(b.getvalue())";
      const python=process.env.CUTY_RENDER_PYTHON || "python";
      const result=spawnSync(python,["-c",encoder],{input:JSON.stringify(frames),maxBuffer:32*1024*1024});
      if(result.status!==0) throw new Error(`Pillow WebP encoding failed: ${result.stderr}`);
      writeFileSync(`public/assembly/fixed-${stage}.webp`,result.stdout);
    }
  }
} finally { await browser.close(); }

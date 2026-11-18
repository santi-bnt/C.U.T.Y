// Start Vite first; render 18 illustrative stills from the current GLB.
/* global document, window */
import { chromium } from "@playwright/test";
import { writeFileSync } from "node:fs";
import { Buffer } from "node:buffer";
import process from "node:process";
const base=process.env.CUTY_RENDER_URL || "http://127.0.0.1:5188";
const executablePath=process.env.CUTY_BROWSER_PATH || (process.platform==="win32" ? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" : undefined);
const browser=await chromium.launch({executablePath,args:["--enable-unsafe-swiftshader"]});
try {
  const page=await browser.newPage({viewport:{width:1050,height:930},deviceScaleFactor:1});
  page.on("pageerror",error=>process.stderr.write(error.stack+"\n"));
  await page.goto(base+"/scripts/assembly-render.html");
  await page.waitForFunction(()=>document.body.dataset.ready==="true",{timeout:60000});
  for(let i=0;i<18;i++) {
    const data=await page.evaluate(stage=>{
      window.renderAssemblyStage(stage);
      return document.querySelector("canvas").toDataURL("image/webp",0.92).split(",")[1];
    },i);
    writeFileSync(`public/assembly/fixed-${String(i+1).padStart(2,"0")}.webp`,Buffer.from(data,"base64"));
  }
} finally { await browser.close(); }

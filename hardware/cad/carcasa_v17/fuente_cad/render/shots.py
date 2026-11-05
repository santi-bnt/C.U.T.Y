"""Render views of a GLB with three.js in headless Chromium.

python3 shots.py <glb relative to cad/> <out_prefix> view1[:params] view2 ...
params use '&' style, e.g.  front34  "side:xray=body_"  "front34:hide=body_&zoom=0.8"
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]          # .../cad
PORT = 8765


def ensure_server():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/render/render.html", timeout=1)
        return
    except Exception:
        pass
    subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/render/render.html", timeout=1)
            return
        except Exception:
            time.sleep(0.1)


def main():
    glb, prefix, *views = sys.argv[1:]
    ensure_server()
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        for v in views:
            name, _, params = v.partition(":")
            w = 1100
            h = 1100
            url = f"http://127.0.0.1:{PORT}/render/render.html?glb=/{glb}&view={name}&w={w}&h={h}"
            if params:
                url += "&" + params
            pg = b.new_page(viewport={"width": w, "height": h})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(url)
            pg.wait_for_function("window.__done === true", timeout=180000)
            tag = name + ("_" + params.replace("=", "-").replace("&", "_").replace(",", "+")[:40] if params else "")
            out = ROOT / f"{prefix}_{tag}.png"
            pg.screenshot(path=str(out))
            print(out.name, errs[:3])
            pg.close()
        b.close()


if __name__ == "__main__":
    main()

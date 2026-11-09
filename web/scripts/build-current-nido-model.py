"""Rebuild the November 6 Nido model from its checked-in CadQuery source."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

WEB = Path(__file__).resolve().parents[1]
ROOT = WEB.parent
CACHE = WEB / "node_modules/.cache/cadquery-builder"
SOURCE = ROOT / "hardware/cad/carcasa_v17/fuente_cad/v17"
PARTS = WEB / "scripts/data/cadquery/parts.json"
BUILD_SOURCE = CACHE / "v17"
OUTPUT = CACHE / "out/cuty_v17_web.glb"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    try:
        import cadquery  # noqa: F401
        import trimesh  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Install build-only CAD tools in this Python environment first: "
            "python -m pip install cadquery trimesh"
        ) from exc

    if not PARTS.is_file():
        raise SystemExit(f"Missing Nido reference dimensions: {PARTS}")
    if not (SOURCE / "build.py").is_file():
        raise SystemExit(f"Missing current CadQuery source: {SOURCE}")

    CACHE.mkdir(parents=True, exist_ok=True)
    if BUILD_SOURCE.exists():
        shutil.rmtree(BUILD_SOURCE)
    shutil.copytree(SOURCE, BUILD_SOURCE)
    shutil.copyfile(PARTS, BUILD_SOURCE / "parts.json")

    # The CAD source defaults to Linux Inter paths. Use an available local font
    # on Windows for the non-structural engraved lettering.
    if os.name == "nt":
        common = BUILD_SOURCE / "common.py"
        text = common.read_text(encoding="utf-8")
        text = text.replace(
            "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
            "C:/Windows/Fonts/arialbd.ttf",
        )
        text = text.replace(
            "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf",
            "C:/Windows/Fonts/arial.ttf",
        )
        common.write_text(text, encoding="utf-8")

    subprocess.run(
        [sys.executable, "-u", str(BUILD_SOURCE / "build.py"), "--rebuild"],
        cwd=ROOT,
        check=True,
    )
    if not OUTPUT.is_file():
        raise SystemExit(f"CadQuery did not produce the expected GLB: {OUTPUT}")
    print(f"Built {OUTPUT} ({OUTPUT.stat().st_size} bytes, sha256 {digest(OUTPUT)})")


if __name__ == "__main__":
    main()

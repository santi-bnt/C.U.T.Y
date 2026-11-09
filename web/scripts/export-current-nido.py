"""Export current November 6 Nido print CAD and source into static web assets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import zipfile

WEB = Path(__file__).resolve().parents[1]
ROOT = WEB.parent
SOURCE = ROOT / "hardware/cad/carcasa_v17"
OUT = WEB / "public/assembly"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_files(bundle: Path, files: list[tuple[Path, str]]) -> None:
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in sorted(files, key=lambda entry: entry[1]):
            info = zipfile.ZipInfo(name, (2026, 11, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    stls = sorted((SOURCE / "STL_imprimir").glob("*.stl"))
    if len(stls) != 30:
        raise SystemExit(f"Expected 30 print STL files, found {len(stls)}")

    shutil.copyfile(SOURCE / "LEEME.md", OUT / "source-readme.md")
    shutil.copyfile(SOURCE / "partes.json", OUT / "print-parts.json")
    shutil.copyfile(SOURCE / "verificacion.json", OUT / "author-cad-verification.json")
    archive_files(
        OUT / "nido-print-stl.zip",
        [(path, f"STL_imprimir/{path.name}") for path in stls],
    )

    code = [path for path in (SOURCE / "fuente_cad").rglob("*") if path.is_file()]
    source_files = [
        (SOURCE / name, name)
        for name in ("LEEME.md", "partes.json", "verificacion.json")
    ] + [(path, path.relative_to(SOURCE).as_posix()) for path in code]
    archive_files(OUT / "current-cad-source.zip", source_files)

    renders = {
        "latest-front.png": "frente_34.png",
        "latest-back.png": "espalda_34.png",
        "latest-side.png": "lado.png",
        "latest-xray.png": "rayos_x.png",
    }
    for output, source in renders.items():
        shutil.copyfile(SOURCE / "renders" / source, OUT / output)

    record_files = [
        SOURCE / "LEEME.md",
        SOURCE / "partes.json",
        SOURCE / "verificacion.json",
        *stls,
        *code,
        *(SOURCE / "renders" / name for name in renders.values()),
    ]
    manifest_path = OUT / "provenance.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest["currentPrintableCad"] = {
        "revision": "V17 Nido · 2026-11-06",
        "source": "hardware/cad/carcasa_v17",
        "stlParts": len(stls),
        "printArchive": "nido-print-stl.zip",
        "sourceArchive": "current-cad-source.zip",
        "report": "author-cad-verification.json",
        "files": [
            {"path": path.relative_to(SOURCE).as_posix(), "sha256": digest(path)}
            for path in sorted(record_files)
        ],
        "reportScope": "Author-supplied CAD/model checks; not independently rerun or physical validation.",
    }
    manifest["webGlbRevision"] = "V17 Nido · 2026-11-05"
    manifest["webGlbPrintCadNote"] = "The interactive model predates the November 6 printable enclosure revision; the latter is shown using supplied renders and downloadable print/source files."
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported current Nido CAD: {len(stls)} STL parts, {len(code)} source files, {len(renders)} renders")


if __name__ == "__main__":
    main()

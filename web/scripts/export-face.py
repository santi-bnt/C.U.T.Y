"""Export offline face atlases from the robot's actual, unchanged renderer.

Run from the repository with an existing Python environment containing Pillow:
raspberry/.venv/Scripts/python.exe web/scripts/export-face.py
Only assets under web/public/face are written; no robot service is started.
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry" / "src"))
from cuty.face.animations import FacePose, expression_target  # noqa: E402
from cuty.face.renderer import FaceRenderer  # noqa: E402

DESTINATION = ROOT / "web" / "public" / "face"
DESTINATION.mkdir(parents=True, exist_ok=True)
renderer = FaceRenderer(480, 320, ssaa=2)
for expression in ("idle", "listening", "happy", "surprised"):
    atlas = Image.new("RGB", (480 * 5, 320 * 8))
    for frame in range(40):
        gaze = frame // 4
        pose = FacePose(
            params=expression_target(expression),
            gaze_x=(-0.7, 0, 0.7)[gaze % 3] if gaze < 9 else 0,
            gaze_y=(-0.5, 0, 0.5)[gaze // 3] if gaze < 9 else 0,
            speech=(frame % 4) / 3,
            openness=1 if gaze < 9 else 0,
        )
        atlas.paste(renderer.render(pose), ((frame % 5) * 480, (frame // 5) * 320))
    path = DESTINATION / f"{expression}.webp"
    atlas.save(path, "WEBP", lossless=True, method=6)
    print(f"{path.relative_to(ROOT)}: {path.stat().st_size:,} bytes")

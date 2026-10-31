"""Verify relocated screen code without importing Linux hardware dependencies."""

import ast
from pathlib import Path
from types import SimpleNamespace

RASPBERRY = Path(__file__).resolve().parents[1]
ROOT = RASPBERRY.parent


def load_function(name, *, method=False, namespace=None):
    tree = ast.parse((RASPBERRY / "touchscreen/cuty_launcher.py").read_text(encoding="utf-8"))
    nodes = tree.body
    if method:
        nodes = next(n for n in nodes if isinstance(n, ast.ClassDef) and n.name == "Launcher").body
    node = next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = namespace if namespace is not None else {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "touchscreen", "exec"), scope)
    return scope[name]


def test_framebuffer_keeps_rgb565_little_endian_output():
    class Framebuffer:
        def open(self, mode, buffering):
            assert mode == "r+b" and buffering == 0
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def write(self, data):
            self.data = bytes(data)

    framebuffer = Framebuffer()
    image = SimpleNamespace(convert=lambda mode: SimpleNamespace(getdata=lambda: [(255, 0, 0), (0, 255, 0)]))
    render = load_function("render_frame", namespace={"W": 2, "H": 1, "FB": framebuffer})
    render(image)
    assert framebuffer.data == b"\x00\xf8\xe0\x07"


def test_calibrated_touch_mapping_and_bounds_are_preserved():
    touch_xy = load_function("touch_xy", method=True, namespace={"W": 480, "H": 320})
    panel = SimpleNamespace(calibration=dict(a=1, b=0, c=0, d=0, e=1, f=0), raw_x=72, raw_y=43)
    assert touch_xy(panel) == (72, 43)
    panel.raw_x, panel.raw_y = -12, 500
    assert touch_xy(panel) == (0, 319)


def test_service_and_compatibility_launch_paths_exist():
    service = (RASPBERRY / "touchscreen/cuty-launcher.service").read_text(encoding="utf-8")
    assert "ExecStart=/usr/bin/python3 -u /home/santi/C.U.T.Y/raspberry/touchscreen/cuty_launcher.py" in service
    for filename in ("cuty.py", "cuty_launcher.py", "cuty_wifi_panel.py"):
        compile((ROOT / filename).read_text(encoding="utf-8"), filename, "exec")
    for filename in ("cuty_launcher.py", "cuty_wifi_panel.py"):
        compile((RASPBERRY / "touchscreen" / filename).read_text(encoding="utf-8"), filename, "exec")

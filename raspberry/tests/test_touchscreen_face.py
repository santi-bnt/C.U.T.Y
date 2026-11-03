"""Run the real launcher face loop headless: fake touch/Wi-Fi panel, file framebuffer."""

import json
import os
import sys
import threading
import time
import types
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("PIL")

TOUCHSCREEN = Path(__file__).resolve().parents[1] / "touchscreen"


@pytest.fixture
def launcher(tmp_path, monkeypatch):
    fb = tmp_path / "fb"
    fb.write_bytes(bytes(480 * 320 * 2))
    read_fd, write_fd = os.pipe()

    class Touch:
        fd = read_fd

        def read(self):
            if not os.read(read_fd, 1):
                raise KeyboardInterrupt  # pipe closed: the launcher's own clean exit
            return []

        def ungrab(self):
            pass

        def close(self):
            pass

    evdev = types.ModuleType("evdev")
    evdev.ecodes = types.SimpleNamespace(EV_ABS=3, ABS_X=0, ABS_Y=1, EV_KEY=1, BTN_TOUCH=330)
    wifi = types.ModuleType("cuty_wifi_panel")
    wifi.W, wifi.H, wifi.FB = 480, 320, fb

    class Panel:
        def __init__(self):
            self.touch, self.screen, self.hotspots = Touch(), "home", []

    wifi.Panel = Panel
    monkeypatch.setitem(sys.modules, "evdev", evdev)
    monkeypatch.setitem(sys.modules, "cuty_wifi_panel", wifi)
    monkeypatch.syspath_prepend(str(TOUCHSCREEN))
    monkeypatch.setenv("CUTY_CAMERA", "off")
    monkeypatch.setenv("CUTY_FACE_LISTEN", "127.0.0.1:0")
    sys.modules.pop("cuty_launcher", None)
    import cuty_launcher

    calibration = tmp_path / "cal.json"
    calibration.write_text(json.dumps(dict(a=1, b=0, c=0, d=0, e=1, f=0)))
    monkeypatch.setattr(cuty_launcher, "CAL_PATH", calibration)
    monkeypatch.setattr(cuty_launcher, "START_MODE", "face")
    app = cuty_launcher.Launcher()
    thread = threading.Thread(target=app.run, daemon=True)
    thread.start()
    yield app, fb
    os.close(write_fd)
    thread.join(2)
    assert not thread.is_alive()
    os.close(read_fd)
    sys.modules.pop("cuty_launcher", None)


def test_face_mode_animates_and_obeys_the_voice(launcher):
    from cuty.face.link import FaceLinkSender

    app, fb = launcher
    deadline = time.monotonic() + 3
    while app.face is None or app.face.pose is None:
        assert time.monotonic() < deadline
        time.sleep(0.02)
    sender = FaceLinkSender(app.link.address)
    sender.expression("surprised", 1.0)
    end = time.monotonic() + 0.6
    while time.monotonic() < end:
        sender.mouth(0.9)
        time.sleep(0.03)
    sender.close()
    assert app.face.animator.expression == "surprised"
    assert app.face.pose.speech > 0.5
    pixels = np.frombuffer(fb.read_bytes(), dtype="<u2").reshape(320, 480)
    assert len(np.unique(pixels)) > 10          # a real picture reached the framebuffer
    teal = ((63 >> 3) << 11) | ((211 >> 2) << 5) | (180 >> 3)
    assert (pixels == teal).sum() > 200          # iris colour is on screen

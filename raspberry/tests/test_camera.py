import sys
import types

import numpy as np

from cuty.vision.camera import FRAME_SIZE, PiCamera


class FakePicamera2:
    instance = None

    def __init__(self):
        self.config = None
        self.calls = []
        FakePicamera2.instance = self

    def create_video_configuration(self, **kwargs):
        self.config = kwargs
        return kwargs

    def configure(self, config):
        self.config = config

    def stream_configuration(self, stream):
        return {"size": self.config[stream]["size"]}

    def start(self): pass
    def stop(self): pass
    def close(self): pass

    def capture_array(self, stream):
        self.calls.append(("single", stream))
        width, height = self.config[stream]["size"]
        return np.zeros((height * 3 // 2, width), dtype=np.uint8)

    def capture_arrays(self, streams):
        self.calls.append(("multiple", tuple(streams)))
        return [self.capture_array(stream) for stream in streams], {"SensorTimestamp": 0}


def install_fake_camera(monkeypatch):
    module = types.ModuleType("picamera2")
    module.Picamera2 = FakePicamera2
    monkeypatch.setitem(sys.modules, "picamera2", module)


def test_default_picamera_configuration_remains_qvga_main(monkeypatch):
    install_fake_camera(monkeypatch)
    camera = PiCamera(high_res_snapshot=False)
    assert camera._cam.config["main"] == {"size": FRAME_SIZE, "format": "YUV420"}
    assert "lores" not in camera._cam.config
    frame = camera.read_frame()
    assert frame.gray.shape == (240, 320)
    assert frame.color_bgr is None
    camera.close()


def test_opt_in_high_resolution_uses_one_camera_and_captures_both_streams_on_request(monkeypatch):
    install_fake_camera(monkeypatch)
    fake_cv2 = types.SimpleNamespace(
        COLOR_YUV2BGR_I420=1,
        cvtColor=lambda image, _code: np.zeros((972, 1296, 3), dtype=np.uint8),
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    camera = PiCamera(high_res_snapshot=True)
    instance = FakePicamera2.instance
    assert instance.config["main"]["size"] == (1296, 972)
    assert instance.config["lores"]["size"] == FRAME_SIZE

    tracking_frame = camera.read_frame()
    assert tracking_frame.gray.shape == (240, 320)
    assert tracking_frame.color_bgr is None
    assert instance.calls[-1] == ("single", "lores")

    requested_frame = camera.read_frame(include_color=True)
    assert requested_frame.gray.shape == (240, 320)
    assert requested_frame.color_bgr.shape == (972, 1296, 3)
    assert ("multiple", ("main", "lores")) in instance.calls
    camera.close()

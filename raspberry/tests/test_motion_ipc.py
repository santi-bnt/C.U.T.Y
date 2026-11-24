import time

import pytest

from cuty.hardware.motion_ipc import MotionIpcServer


class FakeExecutor:
    def __init__(self):
        self.owner = None
        self.active = False
        self.targets = []
        self.stopped = False

    def claim(self, owner):
        if self.owner not in (None, owner):
            return False
        self.owner = owner
        return True

    def activate(self):
        self.active = True
        return True

    def set_axis_target(self, axis, target, *, owner):
        assert owner == self.owner
        self.targets.append((axis, target))

    def stop(self):
        self.stopped = True
        self.active = False
        self.owner = None


def test_face_follow_ipc_requires_local_enable_and_current_target():
    executor = FakeExecutor()
    server = MotionIpcServer(executor, enabled=False)
    with pytest.raises(RuntimeError):
        server._handle({"type": "arm"})

    server.enabled = True
    assert server._handle({"type": "arm"}) == {"ok": True}
    server._handle({"type": "velocity", "value": 0.5, "time": time.monotonic()})
    assert executor.targets[0][0] == "HEAD_PAN"
    assert abs(executor.targets[0][1]) <= 150

    with pytest.raises(RuntimeError):
        server._handle({"type": "velocity", "value": 0.5, "time": time.monotonic() - 1})
    server._handle({"type": "stop"})
    assert executor.stopped and not server._follow_active


def test_face_follow_ipc_rejects_another_motion_owner():
    executor = FakeExecutor()
    executor.owner = "voice"
    server = MotionIpcServer(executor, enabled=True)
    with pytest.raises(RuntimeError):
        server._handle({"type": "arm"})

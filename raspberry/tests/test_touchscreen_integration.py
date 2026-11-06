"""Verify relocated screen code without importing Linux hardware dependencies."""

import ast
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

RASPBERRY = Path(__file__).resolve().parents[1]


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


def test_service_and_canonical_launch_paths_exist():
    service = (RASPBERRY / "touchscreen/cuty-launcher.service").read_text(encoding="utf-8")
    assert "ExecStart=/usr/bin/python3 -u /home/santi/C.U.T.Y/raspberry/touchscreen/cuty_launcher.py" in service
    assert 'cuty_display.py --wait 60' in service
    assert '/dev/fb1' not in service
    for filename in ("cuty_launcher.py", "cuty_wifi_panel.py", "cuty_display.py"):
        compile((RASPBERRY / "touchscreen" / filename).read_text(encoding="utf-8"), filename, "exec")
    assert (RASPBERRY / "touchscreen/install.sh").is_file()
    assert (RASPBERRY / "src/cuty/__main__.py").is_file()


@pytest.mark.parametrize("code", [0, 1])
def test_finished_voice_returns_to_menu_and_releases_resources(code):
    calls = []
    check = load_function("check_voice", method=True)
    panel = SimpleNamespace(
        mode="face", screen="home", hold_since=1, released_at=2, is_pressed=True,
        voice=SimpleNamespace(process=object(), poll=lambda: code),
        leave_face=lambda: calls.append("stop voice and camera"),
        render=lambda: calls.append("render menu"),
    )
    assert check(panel)
    assert panel.mode == "menu" and panel.screen == "home"
    assert calls == ["stop voice and camera", "render menu"]
    assert panel.ignore_next_release and panel.hold_since is None
    assert bool(panel.voice_error) == bool(code)


def test_active_voice_does_not_leave_the_face():
    check = load_function("check_voice", method=True)
    panel = SimpleNamespace(mode="face", voice=SimpleNamespace(process=object(), poll=lambda: None))
    assert not check(panel)
    assert panel.mode == "face"


def power_panel(result=None, *, close_error=None):
    """Real action handlers, with every OS power command replaced by a recorder."""
    calls = []

    def run(args, timeout):
        calls.append((args, timeout))
        return result

    def leave():
        calls.append("close voice and camera")
        if close_error:
            raise close_error

    panel = SimpleNamespace(
        mode="menu", screen="home", value="hidden password", power_action=None,
        power_error="", power_busy="", leave_face=leave,
        render=lambda: calls.append("render"),
    )
    execute = load_function("execute_power", method=True,
                            namespace={"command": run, "subprocess": subprocess})
    panel.execute_power = lambda: execute(panel)
    action = load_function("action", method=True)
    return panel, lambda act: action(panel, act), calls


@pytest.mark.parametrize("requested", ["poweroff", "reboot"])
def test_power_command_requires_confirmation_and_cannot_run_twice(requested):
    panel, action, calls = power_panel(SimpleNamespace(returncode=0, stderr=""))
    action(("power_confirm",))
    action(("power_menu",))
    assert panel.mode == "power" and panel.screen == "home" and panel.value == ""
    action(("power_confirm",))
    action(("power_request", requested))
    assert panel.screen == "confirm" and panel.power_action == requested
    assert not any(isinstance(call, tuple) for call in calls)
    action(("power_confirm",))
    assert panel.screen == "busy" and panel.power_action is None
    assert calls.index("close voice and camera") < next(i for i, call in enumerate(calls) if isinstance(call, tuple))
    assert [call for call in calls if isinstance(call, tuple)] == [
        (["/usr/bin/systemctl", "--no-block", requested], 8),
    ]
    before = list(calls)
    action(("power_confirm",))
    action(("menu",))
    assert calls == before and panel.screen == "busy"


@pytest.mark.parametrize("cancel", [("power_cancel",), ("menu",)])
def test_cancel_or_back_disarms_shutdown(cancel):
    panel, action, calls = power_panel()
    action(("power_menu",))
    action(("power_request", "poweroff"))
    action(cancel)
    action(("power_confirm",))
    assert panel.power_action is None and panel.screen == "home"
    assert not any(isinstance(call, tuple) for call in calls)


def test_power_rejects_unlisted_commands_and_requests_outside_power_menu():
    panel, action, calls = power_panel()
    action(("power_request", "reboot"))
    assert panel.mode == "menu"
    action(("power_menu",))
    action(("power_request", "reboot; echo unexpected"))
    action(("power_request", "poweroff", "extra"))
    action(("power_confirm",))
    assert panel.screen == "home" and panel.power_action is None
    assert not any(isinstance(call, tuple) for call in calls)


@pytest.mark.parametrize("result", [None, SimpleNamespace(returncode=1, stderr="Access denied")])
def test_failed_system_request_keeps_power_menu_usable(result):
    panel, action, calls = power_panel(result)
    action(("power_menu",))
    action(("power_request", "reboot"))
    action(("power_confirm",))
    assert panel.screen == "home" and panel.power_error
    action(("menu",))
    assert panel.mode == "menu"
    assert len([call for call in calls if isinstance(call, tuple)]) == 1


def test_cleanup_failure_does_not_queue_a_power_command():
    panel, action, calls = power_panel(close_error=OSError("Camera close failed"))
    action(("power_menu",))
    action(("power_request", "poweroff"))
    action(("power_confirm",))
    assert panel.screen == "home" and panel.power_error
    assert not any(isinstance(call, tuple) for call in calls)

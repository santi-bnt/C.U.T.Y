"""Menu child lifetime, privilege drop, and return paths without Pi hardware."""

import signal
import subprocess

import pytest

from cuty.brain import menu_voice
from cuty.brain.menu_voice import MenuVoice


def test_child_runs_as_user_with_project_env_and_is_not_duplicated(tmp_path, monkeypatch):
    python = tmp_path / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.touch()
    calls = []

    class Process:
        def poll(self):
            return None

    def spawn(command, **kwargs):
        calls.append((command, kwargs))
        return Process()

    monkeypatch.setattr(menu_voice.os, "geteuid", lambda: 0, raising=False)
    monkeypatch.setattr(menu_voice.subprocess, "Popen", spawn)
    monkeypatch.setenv("CUTY_AUDIO_REMOTE_OUTPUT", "old-pc:8765")
    monkeypatch.setenv("CUTY_FACE_LISTEN", "127.0.0.1:5005")
    voice = MenuVoice(tmp_path)
    voice.start()
    voice.start()
    assert len(calls) == 1
    command, settings = calls[0]
    assert command == ["runuser", "-u", "santi", "--", str(python), "-u", "-m", "cuty", "--hands-free"]
    assert settings["cwd"] == tmp_path and settings["start_new_session"]
    assert settings["stdin"] == subprocess.DEVNULL
    assert "CUTY_AUDIO_REMOTE_OUTPUT" not in settings["env"]
    assert settings["env"]["PYTHONPATH"] == str(tmp_path / "src")


def test_missing_venv_does_not_try_installing_or_starting(tmp_path, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Should not launch any command")

    monkeypatch.setattr(menu_voice.subprocess, "Popen", unexpected)
    with pytest.raises(RuntimeError, match=".venv"):
        MenuVoice(tmp_path).start()


def test_stop_terminates_the_group_and_reaps_the_child(tmp_path, monkeypatch):
    signals, waits = [], []

    class Process:
        pid = 12345

        def poll(self):
            return None

        def wait(self, timeout):
            waits.append(timeout)

    monkeypatch.setattr(menu_voice.os, "killpg", lambda pid, sig: signals.append((pid, sig)), raising=False)
    voice = MenuVoice(tmp_path)
    voice.process = Process()
    voice.stop()
    voice.stop()
    assert signals == [(12345, signal.SIGTERM)]
    assert waits == [3] and voice.process is None

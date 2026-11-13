"""Own the voice child process; the touchscreen keeps rendering independently."""

from __future__ import annotations

import os
import socket
import signal
import subprocess
from pathlib import Path


class MenuVoice:
    def __init__(self, raspberry: Path, user: str = "santi") -> None:
        self.raspberry = raspberry
        self.user = user
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        python = self.raspberry / ".venv/bin/python"
        if not python.is_file():
            raise RuntimeError("Falta raspberry/.venv; revisa la sesión de voz por SSH.")
        command = [str(python), "-u", "-m", "cuty", "--hands-free"]
        if os.geteuid() == 0:
            command = ["runuser", "-u", self.user, "--", *command]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.raspberry / "src")
        env["CUTY_VISION_USER"] = self.user
        try:
            from cuty.vision.ipc import socket_path_for_user
            env["CUTY_VISION_SOCKET"] = str(socket_path_for_user(self.user))
        except (ImportError, KeyError):
            pass
        # Link only to this menu's local listener, not an old PC configuration.
        env["CUTY_FACE_LINK"] = os.getenv("CUTY_FACE_LISTEN", "127.0.0.1:5005")
        env.pop("CUTY_AUDIO_REMOTE_OUTPUT", None)
        self.process = subprocess.Popen(
            command, cwd=self.raspberry, env=env, stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    def poll(self) -> int | None:
        return None if self.process is None else self.process.poll()

    def interrupt_music(self) -> None:
        """A short touchscreen tap opens listening only while local music is playing."""
        if self.process is None or self.process.poll() is not None:
            return
        from cuty.music.interrupt import interrupt_port

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as command:
            command.sendto(b"listen", ("127.0.0.1", interrupt_port()))

    def stop(self) -> None:
        process, self.process = self.process, None
        if process is None or process.poll() is not None:
            return
        # runuser and Python share a group, so neither remains holding the mic.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=2)

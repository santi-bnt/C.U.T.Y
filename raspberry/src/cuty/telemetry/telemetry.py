"""Endpoint HTTP opcional y de solo lectura para el estado del robot."""

from __future__ import annotations

import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Callable
from urllib.parse import urlsplit


class _LocalTelemetryServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, snapshot, allowed_origin):
        self.snapshot = snapshot
        self.allowed_origin = allowed_origin
        super().__init__(address, handler)


class TelemetryServer:
    """Sirve una instantánea sin rutas de control ni cambios de estado."""

    def __init__(
        self,
        snapshot: Callable[[], dict[str, object]],
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        allowed_origin: str | None = None,
    ) -> None:
        if not ipaddress.ip_address(host).is_loopback:
            raise ValueError("El servidor de telemetría solo puede enlazarse a loopback")
        if not 0 <= port <= 65535:
            raise ValueError("Puerto de telemetría inválido")
        if allowed_origin is not None:
            origin = urlsplit(allowed_origin)
            try:
                origin.port
            except ValueError as error:
                raise ValueError("CUTY_TELEMETRY_ORIGIN tiene un puerto inválido") from error
            if (
                allowed_origin == "*"
                or origin.scheme not in {"http", "https"}
                or not origin.netloc
                or origin.hostname is None
                or origin.path
                or origin.query
                or origin.fragment
                or origin.username
                or origin.password
            ):
                raise ValueError("CUTY_TELEMETRY_ORIGIN debe ser un origen HTTP(S) exacto")
        self._snapshot = snapshot
        self._host = host
        self._port = port
        self._allowed_origin = allowed_origin
        self._server: _LocalTelemetryServer | None = None
        self._thread: Thread | None = None

    @property
    def address(self) -> tuple[str, int] | None:
        if self._server is None:
            return None
        host, port = self._server.server_address[:2]
        return str(host), int(port)

    def start(self) -> tuple[str, int]:
        if self._server is not None:
            address = self.address
            if address is None:
                raise RuntimeError("No se pudo obtener la dirección de telemetría")
            return address
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path != "/api/robot/status":
                    self.send_error(404)
                    return
                try:
                    payload = json.dumps(
                        owner._snapshot(), ensure_ascii=False, separators=(",", ":"),
                    ).encode("utf-8")
                except Exception:
                    self.send_error(503, "telemetry unavailable")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                origin = self.headers.get("Origin")
                if owner._allowed_origin and origin == owner._allowed_origin:
                    self.send_header("Access-Control-Allow-Origin", owner._allowed_origin)
                    self.send_header("Vary", "Origin")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format: str, *_args) -> None:
                return

        self._server = _LocalTelemetryServer(
            (self._host, self._port), Handler, self._snapshot, self._allowed_origin,
        )
        self._thread = Thread(
            target=self._server.serve_forever, name="cuty-telemetry-http", daemon=True,
        )
        self._thread.start()
        address = self.address
        if address is None:
            raise RuntimeError("No se pudo obtener la dirección de telemetría")
        return address

    def stop(self) -> None:
        server, self._server = self._server, None
        thread, self._thread = self._thread, None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=1.0)

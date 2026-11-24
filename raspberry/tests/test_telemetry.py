import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cuty.telemetry.telemetry import TelemetryServer


def test_telemetry_server_is_loopback_read_only_and_returns_current_snapshot():
    server = TelemetryServer(
        lambda: {"connection": "offline", "moving": False}, port=0,
    )
    address = server.start()
    try:
        with urlopen(f"http://{address[0]}:{address[1]}/api/robot/status") as response:
            assert response.status == 200
            assert response.headers["Cache-Control"] == "no-store"
            assert json.load(response) == {"connection": "offline", "moving": False}
        with pytest.raises(HTTPError, match="404"):
            urlopen(f"http://{address[0]}:{address[1]}/api/robot/move")
    finally:
        server.stop()


def test_telemetry_server_rejects_network_bind_addresses():
    with pytest.raises(ValueError, match="loopback"):
        TelemetryServer(lambda: {}, host="0.0.0.0")


def test_telemetry_server_requires_an_exact_cors_origin():
    with pytest.raises(ValueError, match="origen HTTP"):
        TelemetryServer(lambda: {}, allowed_origin="*")

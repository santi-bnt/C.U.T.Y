"""Spotify catalog search plus Spotify's official Soloist playback daemon."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from typing import Any
from urllib.parse import urlparse

import httpx
import websockets

from cuty.music.protocol import MusicTrack, PlaybackState


class SpotifySoloistError(RuntimeError):
    """Spotify catalog or local Soloist daemon is unavailable."""


class SpotifySoloistProvider:
    """Control a local Soloist WebSocket and search the Spotify catalog.

    Soloist streams audio itself. This adapter sends only track URIs and
    playback commands; it never downloads or decodes Spotify audio.
    """

    external_output = True

    def __init__(self, websocket_url: str, client_id: str, client_secret: str,
                 *, market: str = "MX", request_timeout: float = 8.0) -> None:
        parsed = urlparse(websocket_url)
        if parsed.scheme != "ws" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Soloist WebSocket must use ws://localhost or ws://127.0.0.1.")
        self.websocket_url = websocket_url
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify Web API client ID and secret are required for voice search.")
        self.market = market.strip().upper() or "MX"
        self.request_timeout = max(2.0, min(20.0, float(request_timeout)))
        self._http = httpx.AsyncClient(timeout=self.request_timeout)
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._tracks: dict[str, MusicTrack] = {}
        self._volume = 70
        self._closed = False

    @classmethod
    def from_env(cls) -> "SpotifySoloistProvider":
        return cls(
            os.getenv("CUTY_SPOTIFY_SOLOIST_WS", "ws://127.0.0.1:9090"),
            os.getenv("CUTY_SPOTIFY_CLIENT_ID", ""),
            os.getenv("CUTY_SPOTIFY_CLIENT_SECRET", ""),
            market=os.getenv("CUTY_SPOTIFY_MARKET", "MX"),
            request_timeout=float(os.getenv("CUTY_SPOTIFY_TIMEOUT", "8")),
        )

    async def _token(self) -> str:
        if self._access_token and time.monotonic() < self._token_expires_at - 30:
            return self._access_token
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        ).decode("ascii")
        try:
            response = await self._http.post(
                "https://accounts.spotify.com/api/token",
                headers={"Authorization": f"Basic {credentials}"},
                data={"grant_type": "client_credentials"},
            )
            response.raise_for_status()
            payload = response.json()
            self._access_token = str(payload["access_token"])
            self._token_expires_at = time.monotonic() + float(payload.get("expires_in", 3600))
            return self._access_token
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise SpotifySoloistError("No pude autenticar la búsqueda del catálogo de Spotify.") from exc

    async def search_tracks(self, query: str) -> list[MusicTrack]:
        if not isinstance(query, str) or not query.strip() or len(query) > 160:
            return []
        token = await self._token()
        try:
            response = await self._http.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query.strip(), "type": "track", "limit": 10, "market": self.market},
            )
            response.raise_for_status()
            items = response.json().get("tracks", {}).get("items", [])
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                self._access_token = None
            raise SpotifySoloistError(f"La búsqueda de Spotify falló (HTTP {exc.response.status_code}).") from exc
        except httpx.HTTPError as exc:
            raise SpotifySoloistError("No pude conectar con la búsqueda de Spotify.") from exc

        results: list[MusicTrack] = []
        for item in items:
            uri = item.get("uri")
            title = item.get("name")
            artists = ", ".join(artist.get("name", "") for artist in item.get("artists", []))
            if not uri or not title:
                continue
            track = MusicTrack(uri, title, artists or "Artista desconocido",
                               (item.get("duration_ms") or 0) / 1000 or None)
            self._tracks[track.id] = track
            results.append(track)
        return results

    async def get_track(self, track_id: str) -> MusicTrack | None:
        return self._tracks.get(track_id)

    async def _request(self, command: str, **fields: Any) -> dict[str, Any]:
        if self._closed:
            raise SpotifySoloistError("El control de Spotify ya se cerró.")
        try:
            async with asyncio.timeout(self.request_timeout):
                async with websockets.connect(self.websocket_url, open_timeout=self.request_timeout,
                                              close_timeout=1, max_size=1_000_000) as socket:
                    # The first event is auth_state; do not issue playback commands before pairing.
                    while True:
                        event = await socket.recv()
                        payload = json.loads(event)
                        if payload.get("type") == "auth_state":
                            if not payload.get("logged_in"):
                                raise SpotifySoloistError(
                                    "Spotify Soloist no está vinculado. Inícialo y autorízalo desde la app de Spotify."
                                )
                            break
                        if payload.get("type") == "error":
                            raise SpotifySoloistError(str(payload.get("message", "Soloist respondió con error.")))
                    await socket.send(json.dumps({
                        "type": "command", "command": command, **fields,
                    }))
                    expected = "playback_state" if command == "get_state" else "command_result"
                    while True:
                        payload = json.loads(await socket.recv())
                        if payload.get("type") == "error":
                            raise SpotifySoloistError(str(payload.get("message", "Soloist respondió con error.")))
                        if payload.get("type") == expected:
                            return payload
        except SpotifySoloistError:
            raise
        except (OSError, TimeoutError, websockets.WebSocketException, ValueError) as exc:
            raise SpotifySoloistError(
                "No pude contactar Spotify Soloist en " + self.websocket_url + "."
            ) from exc

    async def play(self, track_id: str) -> None:
        if not track_id.startswith("spotify:track:"):
            raise ValueError("Spotify Soloist can only start a Spotify track URI here.")
        await self._request("play", uri=track_id)

    async def pause(self) -> None:
        await self._request("pause")

    async def resume(self) -> None:
        await self._request("activate")
        await self._request("play")

    async def stop(self) -> None:
        # Soloist has no stop command: pause and deactivate its Connect device.
        await self._request("pause")
        await self._request("deactivate")

    async def next(self) -> None:
        await self._request("skip_next")

    async def previous(self) -> None:
        await self._request("skip_prev")

    async def set_volume(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError("Volume must be an integer from 0 to 100.")
        await self._request("set_volume", volume=value)
        self._volume = value

    async def get_playback_state(self) -> PlaybackState:
        try:
            payload = await self._request("get_state")
        except SpotifySoloistError:
            # Soloist can be offline/unpaired without disabling Gemini voice mode.
            return PlaybackState("stopped", None, self._volume)
        item = payload.get("item") or {}
        decorations = item.get("decorations") or {}
        identity = decorations.get("identity") or {}
        creators = decorations.get("creators") or []
        artist = ", ".join(
            creator.get("entity", {}).get("decorations", {}).get("identity", {}).get("name", "")
            for creator in creators
        ).strip(", ") or "Artista desconocido"
        track = None
        if item.get("uri") and identity.get("name"):
            playback = decorations.get("playback") or {}
            track = MusicTrack(item["uri"], identity["name"], artist,
                               playback.get("duration_ms", 0) / 1000 or None)
            self._tracks[track.id] = track
        status = payload.get("status", "idle")
        if status == "buffering":
            status = "playing"
        if status == "idle" or not payload.get("is_active", False):
            status = "stopped"
        position = payload.get("position") or {}
        self._volume = int(payload.get("volume", self._volume))
        return PlaybackState(status, track, self._volume,
                             float(position.get("position_ms", 0)) / 1000)

    async def wait_until_finished(self) -> None:
        while True:
            state = await self.get_playback_state()
            if state.status != "playing":
                return
            await asyncio.sleep(0.75)

    async def close(self) -> None:
        self._closed = True
        await self._http.aclose()

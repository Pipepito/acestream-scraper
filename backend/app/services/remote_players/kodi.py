"""Kodi JSON-RPC (HTTP) driver."""
from __future__ import annotations

from typing import Any, Optional

import httpx

from .base import (
    PlayerAuthError,
    PlayerCommandError,
    PlayerProbe,
    PlayerStatus,
    PlayerUnreachable,
    guard,
    new_client,
)

WRONG_PASSWORD_HINT = "Check the Kodi username and password (Settings > Services > Control)."


class KodiDriver:
    def __init__(
        self,
        host: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
        client: Optional[httpx.Client] = None,
    ):
        self.host = host
        self.port = int(port)
        self.username = username or "kodi"
        self.password = password or ""
        self._client = client or new_client()

    def _rpc(self, method: str, params: Optional[dict] = None) -> Any:
        guard(self.host)
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            payload["params"] = params
        try:
            response = self._client.post(
                f"http://{self.host}:{self.port}/jsonrpc",
                json=payload,
                auth=(self.username, self.password),
            )
        except httpx.HTTPError as exc:
            raise PlayerUnreachable(f"Kodi at {self.host}:{self.port} did not answer: {exc}") from exc
        if response.status_code == 401:
            raise PlayerAuthError("wrong_password", WRONG_PASSWORD_HINT)
        if response.status_code >= 400:
            raise PlayerCommandError(f"Kodi answered HTTP {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise PlayerCommandError("Kodi returned a non-JSON response") from exc
        if isinstance(body, dict) and body.get("error"):
            raise PlayerCommandError(str(body["error"].get("message") or body["error"]))
        return body.get("result") if isinstance(body, dict) else body

    def _active_player_id(self) -> Optional[int]:
        players = self._rpc("Player.GetActivePlayers") or []
        return int(players[0]["playerid"]) if players else None

    def probe(self) -> PlayerProbe:
        try:
            props = self._rpc("Application.GetProperties", {"properties": ["version"]}) or {}
        except PlayerAuthError as exc:
            return PlayerProbe(
                reachable=True, authenticated=False, version=None, message=str(exc), hint=str(exc)
            )
        version = props.get("version") or {}
        version_text = f"{version.get('major')}.{version.get('minor')}" if version else None
        return PlayerProbe(
            reachable=True, authenticated=True, version=version_text, message="Kodi is reachable"
        )

    def status(self) -> PlayerStatus:
        player_id = self._active_player_id()
        app = self._rpc("Application.GetProperties", {"properties": ["volume"]}) or {}
        volume = app.get("volume")
        if player_id is None:
            return PlayerStatus(state="stopped", volume_pct=volume)
        props = (
            self._rpc(
                "Player.GetProperties",
                {"playerid": player_id, "properties": ["time", "totaltime", "speed"]},
            )
            or {}
        )
        item = (
            self._rpc("Player.GetItem", {"playerid": player_id, "properties": ["title", "file"]})
            or {}
        ).get("item") or {}
        return PlayerStatus(
            state="playing" if props.get("speed") else "paused",
            title=item.get("title") or item.get("label") or item.get("file"),
            position_s=_seconds(props.get("time")),
            length_s=_seconds(props.get("totaltime")) or None,
            volume_pct=volume,
        )

    def play(self, url: str, title: str) -> None:
        self._rpc("Player.Open", {"item": {"file": url}})

    def _play_pause(self, play: bool) -> None:
        player_id = self._active_player_id()
        if player_id is None:
            raise PlayerCommandError("Nothing is playing on Kodi")
        self._rpc("Player.PlayPause", {"playerid": player_id, "play": play})

    def pause(self) -> None:
        self._play_pause(False)

    def resume(self) -> None:
        self._play_pause(True)

    def stop(self) -> None:
        player_id = self._active_player_id()
        if player_id is None:
            return
        self._rpc("Player.Stop", {"playerid": player_id})

    def set_volume(self, pct: int) -> None:
        self._rpc("Application.SetVolume", {"volume": max(0, min(100, int(pct)))})


def _seconds(value: Optional[dict]) -> Optional[int]:
    if not value:
        return None
    return (
        int(value.get("hours", 0)) * 3600
        + int(value.get("minutes", 0)) * 60
        + int(value.get("seconds", 0))
    )

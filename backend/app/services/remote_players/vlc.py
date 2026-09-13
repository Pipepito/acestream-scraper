"""VLC Lua HTTP interface driver (VLC 3.x/4.x desktop)."""
from __future__ import annotations

import re
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

VLC_MAX_VOLUME = 512  # 256 = 100 %, 512 = VLC's 200 % GUI ceiling
NO_PASSWORD_HINT = (
    "VLC's web interface has no password. In VLC: Tools > Preferences > All > Interface > "
    "Main interfaces > Web, then Lua > Lua HTTP > Password."
)
WRONG_PASSWORD_HINT = "Check the password (VLC: Lua HTTP password)."
_PRE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.S | re.I)


class VlcDriver:
    def __init__(
        self,
        host: str,
        port: int,
        password: Optional[str],
        client: Optional[httpx.Client] = None,
    ):
        self.host = host
        self.port = int(port)
        self.password = password or ""
        self._client = client or new_client()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _request(self, command: Optional[str] = None, **params: Any) -> dict:
        guard(self.host)
        query = {}
        if command:
            query["command"] = command
        query.update({k: v for k, v in params.items() if v is not None})
        try:
            response = self._client.get(
                f"{self.base_url}/requests/status.json", params=query, auth=("", self.password)
            )
        except httpx.HTTPError as exc:
            raise PlayerUnreachable(f"VLC at {self.host}:{self.port} did not answer: {exc}") from exc
        if response.status_code == 403:
            raise PlayerAuthError("no_password", NO_PASSWORD_HINT)
        if response.status_code == 401:
            raise PlayerAuthError("wrong_password", WRONG_PASSWORD_HINT)
        if response.status_code >= 400:
            raise PlayerCommandError(f"VLC answered HTTP {response.status_code}")
        content_type = response.headers.get("Content-Type", "")
        if "html" in content_type or response.text.lstrip().startswith("<"):
            match = _PRE.search(response.text)
            raise PlayerCommandError(
                (match.group(1).strip() if match else "VLC reported an error").replace("\n", " ")[:300]
            )
        try:
            return response.json()
        except ValueError as exc:
            raise PlayerCommandError("VLC returned a non-JSON status") from exc

    def probe(self) -> PlayerProbe:
        try:
            status = self._request()
        except PlayerAuthError as exc:
            return PlayerProbe(
                reachable=True, authenticated=False, version=None, message=str(exc), hint=str(exc)
            )
        return PlayerProbe(
            reachable=True,
            authenticated=True,
            version=status.get("version"),
            message="VLC is reachable",
        )

    def status(self) -> PlayerStatus:
        data = self._request()
        meta = ((data.get("information") or {}).get("category") or {}).get("meta") or {}
        state = data.get("state") or "stopped"
        if state not in ("playing", "paused", "stopped"):
            state = "stopped"
        volume = data.get("volume")
        return PlayerStatus(
            state=state,
            title=meta.get("title") or meta.get("filename"),
            position_s=int(data["time"]) if data.get("time") is not None else None,
            length_s=int(data["length"]) if data.get("length") else None,
            volume_pct=round(int(volume) * 100 / 256) if volume is not None else None,
        )

    def play(self, url: str, title: str) -> None:
        self._request("pl_empty")
        self._request("in_play", input=url)

    def pause(self) -> None:
        self._request("pl_forcepause")

    def resume(self) -> None:
        self._request("pl_forceresume")

    def stop(self) -> None:
        self._request("pl_stop")

    def set_volume(self, pct: int) -> None:
        raw = max(0, min(VLC_MAX_VOLUME, round(int(pct) * 256 / 100)))
        self._request("volume", val=str(raw))

"""Plex Media Server: identity, DVR lookup and guide reload (undocumented owner-token API)."""
from __future__ import annotations

from typing import Any, List, Optional
from urllib.parse import urlsplit

import httpx

from .base import MediaServerUnreachable, decode_json, guard, new_client, raise_for


class PlexClient:
    def __init__(self, base_url: str, token: Optional[str], client: Optional[httpx.Client] = None):
        self.base_url = base_url.rstrip("/")
        self.host = urlsplit(self.base_url).hostname or ""
        self.token = token or ""
        self._client = client or new_client()

    def _request(self, method: str, path: str, *, auth: bool = True) -> httpx.Response:
        guard(self.host)
        headers = {"Accept": "application/json"}
        if auth:
            headers["X-Plex-Token"] = self.token
        try:
            response = self._client.request(method, f"{self.base_url}{path}", headers=headers)
        except httpx.HTTPError as exc:
            raise MediaServerUnreachable(f"Plex at {self.base_url} did not answer: {exc}") from exc
        raise_for(response, f"{method} {path}")
        return response

    def _json(self, method: str, path: str, *, auth: bool = True) -> Any:
        return decode_json(self._request(method, path, auth=auth), f"{method} {path}")

    def identity(self) -> dict:
        return (self._json("GET", "/identity", auth=False) or {}).get("MediaContainer", {})

    def dvrs(self) -> List[dict]:
        return ((self._json("GET", "/livetv/dvrs") or {}).get("MediaContainer", {}) or {}).get("Dvr", []) or []

    def find_dvr_key(self, device_id: str) -> Optional[str]:
        """The DVR whose HDHomeRun grabber points at our advertised device id."""
        needle = f"tv.plex.grabbers.hdhomerun/{device_id}".lower()
        for dvr in self.dvrs():
            for device in dvr.get("Device", []) or []:
                if needle in str(device.get("uri", "")).lower():
                    return str(dvr.get("key"))
        return None

    def reload_guide(self, dvr_key: str) -> None:
        self._request("POST", f"/livetv/dvrs/{dvr_key}/reloadGuide")

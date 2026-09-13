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
        expected_id = device_id.strip().lower()
        if not expected_id:
            return None
        expected_uri = f"device://tv.plex.grabbers.hdhomerun/{expected_id}"
        for dvr in self.dvrs():
            for device in dvr.get("Device", []) or []:
                # Plex reports the HTTP tuner address in uri and the HDHR
                # identity in uuid/deviceId. Retain the older uri form too.
                matches = str(device.get("deviceId", "")).strip().lower() == expected_id or any(
                    str(device.get(field, "")).strip().lower() == expected_uri
                    for field in ("uuid", "uri")
                )
                if matches and dvr.get("key") is not None:
                    return str(dvr["key"])
        return None

    def reload_guide(self, dvr_key: str) -> None:
        self._request("POST", f"/livetv/dvrs/{dvr_key}/reloadGuide")

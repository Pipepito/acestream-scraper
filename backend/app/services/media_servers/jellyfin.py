"""Jellyfin 10.9+ Live TV configuration client."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import httpx

from .base import MediaServerUnreachable, decode_json, guard, new_client, raise_for


class JellyfinClient:
    def __init__(self, base_url: str, api_key: Optional[str], device_id: str, app_version: str, client: Optional[httpx.Client] = None):
        self.base_url = base_url.rstrip("/")
        self.host = urlsplit(self.base_url).hostname or ""
        self.api_key = api_key or ""
        self.device_id = device_id
        self.app_version = app_version
        self._client = client or new_client()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f'MediaBrowser Token="{self.api_key}", Client="acestream-scraper", Device="acestream-scraper", DeviceId="{self.device_id}", Version="{self.app_version}"',
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, *, params: Optional[dict] = None, json: Any = None, auth: bool = True) -> httpx.Response:
        guard(self.host)
        try:
            response = self._client.request(method, f"{self.base_url}{path}", params=params, json=json, headers=self._headers() if auth else {"Accept": "application/json"})
        except httpx.HTTPError as exc:
            raise MediaServerUnreachable(f"Jellyfin at {self.base_url} did not answer: {exc}") from exc
        raise_for(response, f"{method} {path}")
        return response

    def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        return decode_json(self._request(method, path, **kwargs), f"{method} {path}")

    def public_info(self) -> dict:
        return self._json("GET", "/System/Info/Public", auth=False)

    def livetv_config(self) -> dict:
        return self._json("GET", "/System/Configuration/livetv")

    def save_tuner_host(self, payload: dict) -> dict:
        return self._json("POST", "/LiveTv/TunerHosts", json=payload)

    def delete_tuner_host(self, tuner_id: str) -> None:
        self._request("DELETE", "/LiveTv/TunerHosts", params={"id": tuner_id})

    def save_listing_provider(self, payload: dict) -> dict:
        return self._json("POST", "/LiveTv/ListingProviders", params={"validateListings": "false", "validateLogin": "false"}, json=payload)

    def delete_listing_provider(self, provider_id: str) -> None:
        self._request("DELETE", "/LiveTv/ListingProviders", params={"id": provider_id})

    def scheduled_tasks(self) -> List[dict]:
        return self._json("GET", "/ScheduledTasks")

    def start_task(self, task_id: str) -> None:
        self._request("POST", f"/ScheduledTasks/Running/{task_id}")

    def channel_count(self) -> int:
        body = self._json("GET", "/LiveTv/Channels", params={"addCurrentProgram": "false", "enableImages": "false", "limit": "1"})
        return int((body or {}).get("TotalRecordCount") or 0)

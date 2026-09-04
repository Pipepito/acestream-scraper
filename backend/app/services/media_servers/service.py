"""Jellyfin/Plex registration, refresh and fingerprint-driven sync (spec 7.3)."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from urllib.parse import urlsplit

import httpx
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.models import MediaServer
from app.repositories.media_server_repository import MediaServerRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.tuner_service import TunerService
from app.utils.url_guard import validate_lan_target

from .base import MediaServerAuthError, MediaServerError, MediaServerUnreachable, new_client
from .jellyfin import JellyfinClient
from .plex import PlexClient

# Sent to Jellyfin as the client version. Not read from version.txt: the file
# stays outside the image (only backend/ is copied), so a lookup would fail at
# runtime for a string Jellyfin only ever logs.
APP_VERSION = "2.0.0"
# Jellyfin answers 503 while Live TV is still starting up; one retry clears it.
BUSY_RETRY_SECONDS = 2.0

PLEX_STEPS = [
    "In Plex Web open Settings > Live TV & DVR and choose Set Up Plex Tuner (Plex Pass is required).",
    "Click \"Don't see your HDHomeRun device? Enter its network address manually\" and paste the tuner address.",
    "Pick any country, then choose \"Have an XMLTV guide on your server?\" and paste the guide URL.",
    "Review the channel mapping and finish. After channels change here, use Manage Channels > Rescan in Plex (or add a Plex token so the guide refreshes automatically).",
]


@dataclass
class RefreshResult:
    status: str  # ok | error | manual
    message: Optional[str] = None


class MediaServerService:
    def __init__(self, db: Session, *, client_factory: Callable[[], httpx.Client] = new_client, settings_getter: Callable = get_settings):
        self.db = db
        self.repo = MediaServerRepository(db)
        self._client_factory = client_factory
        self._settings = settings_getter

    # --- validation --------------------------------------------------------------
    def validate_base_url(self, value: str) -> str:
        candidate = (value or "").strip().rstrip("/")
        parts = urlsplit(candidate)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("base_url must be http(s)://host[:port][/path] without credentials")
        validate_lan_target(parts.hostname, resolve=False)
        return candidate

    # --- clients -----------------------------------------------------------------
    def _jellyfin(self, base_url: str, api_key: Optional[str]) -> JellyfinClient:
        return JellyfinClient(base_url, api_key, TunerService(self.db).device_id(), APP_VERSION, client=self._client_factory())

    def _plex(self, base_url: str, token: Optional[str]) -> PlexClient:
        return PlexClient(base_url, token, client=self._client_factory())

    def _secret(self, api_key: Optional[str], stored_id: Optional[int]) -> Optional[str]:
        if api_key:
            return api_key
        if stored_id is not None:
            stored = self.repo.get(stored_id)
            if stored is not None:
                return stored.api_key
        return None

    def _public_base_url(self) -> str:
        """The origin the media server must fetch us on: the operator's setting,
        falling back to the PUBLIC_BASE_URL env seed."""
        return (SettingsRepository(self.db).get_setting(SettingsRepository.PUBLIC_BASE_URL) or "").strip().rstrip("/")

    # --- use cases -----------------------------------------------------------------
    def test(self, kind: str, base_url: str, api_key: Optional[str], stored_id: Optional[int] = None) -> dict:
        secret = self._secret(api_key, stored_id)
        try:
            if kind == "jellyfin":
                client = self._jellyfin(base_url, secret)
                info = client.public_info()
                try:
                    client.livetv_config()
                    authenticated = True
                except MediaServerAuthError:
                    authenticated = False
                return {"reachable": True, "authenticated": authenticated, "version": info.get("Version"),
                        "message": "Jellyfin is reachable" if authenticated else "Jellyfin rejected the API key (it must be an administrator API key from Dashboard > API Keys)"}
            client = self._plex(base_url, secret)
            identity = client.identity()
            authenticated = True
            if secret:
                try:
                    client.dvrs()
                except MediaServerAuthError:
                    authenticated = False
            return {"reachable": True, "authenticated": authenticated, "version": identity.get("version"),
                    "message": "Plex is reachable" if authenticated else "Plex rejected the token"}
        except MediaServerUnreachable as exc:
            return {"reachable": False, "authenticated": False, "version": None, "message": str(exc)}

    def connect(self, server: MediaServer, public_base_url: str) -> MediaServer:
        public = public_base_url.rstrip("/")
        if server.kind == "jellyfin":
            client = self._jellyfin(server.base_url, server.api_key)
            server.server_version = str(client.public_info().get("Version") or "")
            config = client.livetv_config()
            tuner_url = f"{public}/tuner/playlist.m3u" if server.tuner_mode == "m3u" else f"{public}/tuner"
            existing = next((t for t in config.get("TunerHosts", []) if t.get("Id") == server.tuner_host_id or t.get("Url") == tuner_url), None)
            tuner_payload = {
                "Id": (existing or {}).get("Id") or "",
                "Type": "m3u" if server.tuner_mode == "m3u" else "hdhomerun",
                "Url": tuner_url,
                "FriendlyName": TunerService(self.db).settings().friendly_name,
                "TunerCount": 0, "AllowHWTranscoding": False, "AllowStreamSharing": True, "ImportFavoritesOnly": False,
                "EnableStreamLooping": False, "IgnoreDts": True,
            }
            try:
                saved_tuner = client.save_tuner_host(tuner_payload)
            except MediaServerError as exc:
                # Jellyfin validates a tuner by fetching it, so its refusal is
                # almost always a public address it cannot reach (spec 7.3).
                raise MediaServerError(exc.status_code, f"Jellyfin could not download {tuner_url}; check the public address ({exc})") from exc
            server.tuner_host_id = str(saved_tuner["Id"])
            guide_url = f"{public}/tuner/epg.xml" if server.tuner_mode == "m3u" else f"{public}/tuner/guide.xml"
            existing_provider = next((p for p in config.get("ListingProviders", []) if p.get("Id") == server.listing_provider_id or p.get("Path") == guide_url), None)
            provider_payload = {
                "Id": (existing_provider or {}).get("Id") or "",
                "Type": "xmltv", "Path": guide_url, "EnableAllTuners": False, "EnabledTuners": [server.tuner_host_id],
            }
            saved_provider = client.save_listing_provider(provider_payload)
            server.listing_provider_id = str(saved_provider["Id"])
        else:
            client = self._plex(server.base_url, server.api_key)
            server.server_version = str(client.identity().get("version") or "")
            if server.api_key:
                server.dvr_key = client.find_dvr_key(TunerService(self.db).device_id())
        server.last_error = None
        return self.repo.save(server)

    def refresh(self, server: MediaServer) -> RefreshResult:
        if server.kind == "jellyfin":
            client = self._jellyfin(server.base_url, server.api_key)
            try:
                return self._trigger_jellyfin_guide(client)
            except MediaServerError as exc:
                if exc.status_code != 503:
                    raise
                time.sleep(BUSY_RETRY_SECONDS)
                return self._trigger_jellyfin_guide(client)
        if not server.api_key:
            return RefreshResult("manual", "Rescan the guide in Plex (add a Plex token to refresh automatically)")
        client = self._plex(server.base_url, server.api_key)
        if not server.dvr_key:
            server.dvr_key = client.find_dvr_key(TunerService(self.db).device_id())
            self.repo.save(server)
        if not server.dvr_key:
            return RefreshResult("manual", "Plex has no DVR using this tuner yet; add it in Plex Web first")
        client.reload_guide(server.dvr_key)
        return RefreshResult("ok", "Plex is reloading its guide")

    @staticmethod
    def _trigger_jellyfin_guide(client: JellyfinClient) -> RefreshResult:
        task = next((t for t in client.scheduled_tasks() if t.get("Key") == "RefreshGuide"), None)
        if task is None:
            return RefreshResult("error", "Jellyfin has no Refresh Guide task (is Live TV set up?)")
        if str(task.get("State", "")).lower() != "running":
            client.start_task(str(task["Id"]))
        return RefreshResult("ok", "Jellyfin is refreshing its guide")

    def status(self, server: MediaServer) -> dict:
        public = self._public_base_url()
        base = {"connected": False, "channel_count": None, "refresh_state": None, "last_result": None, "steps": [], "paste": {}, "error": None}
        if server.kind == "plex":
            base["connected"] = bool(server.dvr_key)
            base["steps"] = PLEX_STEPS
            host_port = urlsplit(public).netloc if public else "<public address>"
            base["paste"] = {"tuner_address": f"{host_port}/tuner", "guide_url": f"{public or '<public address>'}/tuner/guide.xml", "device_id": TunerService(self.db).device_id()}
            return base
        base["connected"] = bool(server.tuner_host_id and server.listing_provider_id)
        if not base["connected"] or not server.api_key:
            return base
        try:
            client = self._jellyfin(server.base_url, server.api_key)
            task = next((t for t in client.scheduled_tasks() if t.get("Key") == "RefreshGuide"), None)
            base["refresh_state"] = (task or {}).get("State")
            base["last_result"] = ((task or {}).get("LastExecutionResult") or {}).get("Status")
            base["channel_count"] = client.channel_count()
        except (MediaServerUnreachable, MediaServerAuthError, MediaServerError) as exc:
            base["error"] = str(exc)
        return base

    def disconnect(self, server: MediaServer) -> MediaServer:
        if server.kind == "jellyfin":
            client = self._jellyfin(server.base_url, server.api_key)
            if server.listing_provider_id:
                client.delete_listing_provider(server.listing_provider_id)
            if server.tuner_host_id:
                client.delete_tuner_host(server.tuner_host_id)
            server.tuner_host_id = None
            server.listing_provider_id = None
        else:
            server.dvr_key = None
        server.last_sync_status = "never"
        return self.repo.save(server)

    # --- sync ------------------------------------------------------------------------
    def sync_if_changed(self, server: MediaServer) -> Optional[RefreshResult]:
        tuner = TunerService(self.db)
        lineup_fp = tuner.lineup_fingerprint(tuner.build_lineup())
        guide_fp = tuner.guide_fingerprint()
        if lineup_fp == server.last_lineup_fingerprint and guide_fp == server.last_guide_fingerprint:
            return None
        min_minutes = int(self._settings().MEDIA_SERVER_MIN_REFRESH_MINUTES)
        now = datetime.now(timezone.utc)
        if min_minutes and server.last_sync_at and now - server.last_sync_at < timedelta(minutes=min_minutes):
            return None
        try:
            result = self.refresh(server)
        except (MediaServerUnreachable, MediaServerAuthError, MediaServerError) as exc:
            result = RefreshResult("error", str(exc))
        if result.status != "error":
            # A failed pass keeps the stored fingerprints so the next run sees the
            # same change and retries it; advancing them would drop it for good.
            server.last_lineup_fingerprint = lineup_fp
            server.last_guide_fingerprint = guide_fp
        server.last_sync_status = result.status
        server.last_error = result.message if result.status == "error" else None
        if result.status == "ok":
            server.last_sync_at = now
        self.repo.save(server)
        return result

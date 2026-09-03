"""Thin client for the AceStream engine playback API (spec 4.1).

Used by the stream relay (tuner, remote players) and the web player. The
engine URL is the DB setting ``ace_engine_url`` read at call time.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from types import TracebackType
from typing import Optional

import httpx

from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)

START_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
STAT_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


class EngineUnavailableError(RuntimeError):
    """The engine could not be reached or answered with a transport/5xx error."""


class EngineRefusedError(RuntimeError):
    """The engine answered but refused (its JSON carried an ``error``)."""


@dataclass(frozen=True)
class EngineSession:
    content_id: str
    pid: str
    playback_url: str
    stat_url: str
    command_url: str
    is_live: bool


@dataclass(frozen=True)
class EngineStats:
    status: str
    peers: int
    speed_down: int
    speed_up: int


def new_pid() -> str:
    return uuid.uuid4().hex


def engine_url_from_settings(settings_repo: SettingsRepository) -> str:
    url = (settings_repo.get_setting(SettingsRepository.ACE_ENGINE_URL) or "").strip()
    if not url:
        raise EngineUnavailableError("Acestream Engine URL is not configured")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url.rstrip("/")


class EngineClient:
    """Talks to one engine over HTTP.

    When no ``client`` is injected the instance creates — and therefore owns —
    an :class:`httpx.Client`; use it as a context manager (or call
    :meth:`close`) so its connection pool is released. An injected client is
    never closed here: whoever opened it closes it.
    """

    def __init__(self, engine_url: str, client: Optional[httpx.Client] = None):
        self.engine_url = engine_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=START_TIMEOUT)

    def close(self) -> None:
        """Release the connection pool, but only if this instance created it."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "EngineClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def _get_json(self, url: str, params: Optional[dict] = None, timeout: httpx.Timeout = START_TIMEOUT) -> dict:
        try:
            response = self._client.get(url, params=params, timeout=timeout)
        except httpx.HTTPError as exc:
            raise EngineUnavailableError(f"Engine request failed: {exc}") from exc
        if response.status_code >= 500:
            raise EngineUnavailableError(f"Engine returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise EngineUnavailableError("Engine returned a non-JSON response") from exc
        error = payload.get("error") if isinstance(payload, dict) else None
        if error:
            raise EngineRefusedError(str(error))
        body = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(body, dict):
            raise EngineUnavailableError("Engine response has no 'response' object")
        return body

    def start(self, content_id: str, pid: Optional[str] = None) -> EngineSession:
        pid = pid or new_pid()
        body = self._get_json(
            f"{self.engine_url}/ace/getstream",
            params={"id": content_id, "pid": pid, "format": "json"},
        )
        try:
            return EngineSession(
                content_id=content_id,
                pid=pid,
                playback_url=str(body["playback_url"]),
                stat_url=str(body["stat_url"]),
                command_url=str(body["command_url"]),
                is_live=bool(int(body.get("is_live") or 0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise EngineUnavailableError(f"Engine start response is incomplete: {body}") from exc

    def stop(self, session: EngineSession) -> None:
        # Merge rather than replace: the engine may hand back a command_url
        # that already carries a token or session id in its query.
        url = httpx.URL(session.command_url).copy_merge_params({"method": "stop"})
        try:
            self._client.get(url, timeout=STAT_TIMEOUT)
        except httpx.HTTPError as exc:
            logger.warning("Engine stop for %s failed: %s", session.content_id, exc)

    def stat(self, session: EngineSession) -> EngineStats:
        body = self._get_json(session.stat_url, timeout=STAT_TIMEOUT)
        return EngineStats(
            status=str(body.get("status") or "unknown"),
            peers=int(body.get("peers") or 0),
            speed_down=int(body.get("speed_down") or 0),
            speed_up=int(body.get("speed_up") or 0),
        )

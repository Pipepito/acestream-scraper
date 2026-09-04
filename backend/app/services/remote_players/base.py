"""Shared types for remote player drivers (spec 6.2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Protocol

import httpx

from app.utils.url_guard import BlockedURLError, validate_lan_target

AuthErrorKind = Literal["no_password", "wrong_password"]
PlayerStateValue = Literal["playing", "paused", "stopped"]
DRIVER_TIMEOUT = httpx.Timeout(5.0, connect=2.0)


class PlayerUnreachable(RuntimeError):
    """No usable TCP/HTTP answer from the player."""


class PlayerAuthError(RuntimeError):
    """The player answered but rejected the credentials we sent."""

    def __init__(self, kind: AuthErrorKind, message: str):
        super().__init__(message)
        self.kind: AuthErrorKind = kind


class PlayerCommandError(RuntimeError):
    """The player answered but refused or failed the command."""


@dataclass
class PlayerProbe:
    reachable: bool
    authenticated: bool
    version: Optional[str]
    message: str
    hint: Optional[str] = None


@dataclass
class PlayerStatus:
    state: PlayerStateValue
    title: Optional[str] = None
    position_s: Optional[int] = None
    length_s: Optional[int] = None
    volume_pct: Optional[int] = None
    message: Optional[str] = None


class PlayerDriver(Protocol):
    def probe(self) -> PlayerProbe: ...

    def status(self) -> PlayerStatus: ...

    def play(self, url: str, title: str) -> None: ...

    def pause(self) -> None: ...

    def resume(self) -> None: ...

    def stop(self) -> None: ...

    def set_volume(self, pct: int) -> None: ...


def new_client() -> httpx.Client:
    return httpx.Client(follow_redirects=False, timeout=DRIVER_TIMEOUT)


def guard(host: str) -> None:
    """Refuse metadata/link-local/multicast targets right before each request."""
    try:
        validate_lan_target(host, resolve=True)
    except BlockedURLError as exc:
        raise PlayerUnreachable(str(exc)) from exc


def make_driver(
    kind: str,
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    client: Optional[httpx.Client] = None,
) -> PlayerDriver:
    if kind == "vlc":
        from .vlc import VlcDriver

        return VlcDriver(host, port, password, client=client)
    if kind == "kodi":
        from .kodi import KodiDriver

        return KodiDriver(host, port, username, password, client=client)
    raise ValueError(f"unknown player kind: {kind}")

"""Remote player use cases (spec 6.1, 6.3)."""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Union

import httpx
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.models import RemotePlayer
from app.repositories.base_url_repository import BaseUrlRepository
from app.repositories.remote_player_repository import RemotePlayerRepository
from app.services.playlist_service import PlaylistService
from app.services.tuner_network import TunerNetworkGate
from app.utils.url_guard import BlockedURLError, validate_lan_target

from .base import PlayerDriver, PlayerProbe, PlayerStatus, make_driver, new_client

COMMANDS = ("pause", "resume", "stop", "volume")
# Characters that would turn a bare host into a URL with a scheme, userinfo,
# path, query, fragment or an already-bracketed authority.
_HOST_DELIMITERS = "/@?#\\[]"
MAX_VOLUME_PCT = 200
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


def _ip_literal(host: str) -> Optional[IPAddress]:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _bare_host(host: str) -> str:
    """Undo the brackets validate_host puts around an IPv6 literal."""
    host = (host or "").strip()
    return host[1:-1] if host.startswith("[") and host.endswith("]") else host


def _same_target(player: RemotePlayer, host: str, port: int) -> bool:
    """True when the saved row already sends its password to this host and port."""
    return int(player.port) == int(port) and (
        _bare_host(player.host).lower() == _bare_host(host).lower()
    )


@dataclass
class TunerAccess:
    """Whether the tuner allowlist lets this player reach the relay URL."""

    addresses: List[str] = field(default_factory=list)
    allowed: bool = True


class RemotePlayerService:
    def __init__(
        self,
        db: Session,
        *,
        client_factory: Callable[[], httpx.Client] = new_client,
        settings_getter: Callable = get_settings,
    ):
        self.db = db
        self.repo = RemotePlayerRepository(db)
        self._client_factory = client_factory
        self._settings = settings_getter

    # --- validation ------------------------------------------------------------
    def validate_host(self, host: str) -> str:
        """A bare hostname or IP — no scheme, credentials, port or path — that is
        not a metadata/link-local/multicast/reserved address. Raises
        BlockedURLError.

        An IPv6 literal comes back bracketed (``fd00::1`` -> ``[fd00::1]``): the
        drivers build ``http://{host}:{port}``, and without the brackets that is
        not a URL httpx can parse."""
        candidate = _bare_host(host)
        if not candidate or any(ch.isspace() or ch in _HOST_DELIMITERS for ch in candidate):
            raise BlockedURLError(
                "Host must be a hostname or IP address without scheme, credentials or path"
            )
        literal = _ip_literal(candidate)
        if literal is None and ":" in candidate:
            raise BlockedURLError(
                "Host must not carry a port or be a partial IPv6 address — use the port field"
            )
        validate_lan_target(candidate, resolve=False)
        if literal is not None and literal.version == 6:
            return f"[{literal.compressed}]"
        return candidate

    def tuner_access(self, host: str) -> TunerAccess:
        """Heuristic for the UI: resolve the player's host and check every
        address against TUNER_ALLOWED_NETWORKS, so we can warn before the
        player gets a 403 from the relay URL. A host we cannot resolve is
        reported as allowed — we have nothing to complain about."""
        gate = TunerNetworkGate(self._settings().TUNER_ALLOWED_NETWORKS)
        try:
            infos = socket.getaddrinfo(_bare_host(host), None, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            return TunerAccess(addresses=[], allowed=True)
        addresses = sorted({info[4][0] for info in infos})
        return TunerAccess(addresses=addresses, allowed=all(gate.is_allowed(a) for a in addresses))

    # --- drivers ---------------------------------------------------------------
    def _driver(
        self, kind: str, host: str, port: int, username: Optional[str], password: Optional[str]
    ) -> PlayerDriver:
        return make_driver(kind, host, port, username, password, client=self._client_factory())

    def driver_for(self, player: RemotePlayer) -> PlayerDriver:
        return self._driver(player.kind, player.host, player.port, player.username, player.password)

    def probe(
        self,
        kind: str,
        host: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
        stored_id: Optional[int] = None,
    ) -> Tuple[PlayerProbe, TunerAccess]:
        """Secret rule: the typed password when non-empty; else the stored one
        when stored_id names a row that already points at this same host and
        port; else probe without credentials.

        A stored password never travels to a target the saved row does not
        already talk to: the API only ever reports has_password, so a caller
        who cannot read the secret back could otherwise post any address and
        have us hand it to a listener of their choosing."""
        secret = password if password else None
        if secret is None and stored_id is not None:
            stored = self.repo.get(stored_id)
            if stored is not None and _same_target(stored, host, port):
                secret = stored.password
        driver = self._driver(kind, host, port, username, secret or "")
        return driver.probe(), self.tuner_access(host)

    def password_for_update(
        self,
        player: RemotePlayer,
        host: Optional[str],
        port: Optional[int],
        password: Optional[str],
    ) -> Optional[str]:
        """The password a PATCH should store: the typed one when given, else the
        stored one — unless the row is being pointed somewhere else, in which
        case it is cleared ("" clears, None keeps; see the repository).

        A player at a new address is a new device. probe() refuses to send a
        stored secret to a host the row does not name, but the row itself can be
        moved: without this rule, PATCH {"host": ...} followed by POST
        /{id}/test hands the secret to any address the caller picks — the very
        thing the API withholding the password is supposed to prevent."""
        if password is not None:
            return password
        return None if _same_target(player, host or player.host, port or player.port) else ""

    def status(self, player: RemotePlayer) -> PlayerStatus:
        return self.driver_for(player).status()

    # --- playback --------------------------------------------------------------
    def resolve_stream_url(self, player: RemotePlayer, content_id: str, public_base_url: str) -> str:
        """The player's own stream link format when it has one, else the
        backend relay URL (spec 6.3)."""
        if player.base_url_id is not None:
            entry = BaseUrlRepository(self.db).get(player.base_url_id)
            if entry is not None:
                return PlaylistService._stream_link(entry.pattern, content_id, None)
        return f"{public_base_url.rstrip('/')}/tuner/stream/{content_id}.ts"

    def play(self, player: RemotePlayer, content_id: str, public_base_url: str, title: str) -> str:
        url = self.resolve_stream_url(player, content_id, public_base_url)
        self.driver_for(player).play(url, title)
        return url

    def command(self, player: RemotePlayer, command: str, value: Optional[int] = None) -> None:
        if command not in COMMANDS:
            raise ValueError(f"unsupported command: {command}")
        driver = self.driver_for(player)
        if command == "pause":
            driver.pause()
        elif command == "resume":
            driver.resume()
        elif command == "stop":
            driver.stop()
        else:
            if value is None:
                raise ValueError("volume needs a value")
            driver.set_volume(max(0, min(MAX_VOLUME_PCT, int(value))))

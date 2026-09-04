# Media Integrations, Plan 3: Remote Players (VLC, Kodi) and the Integrations Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user register VLC and Kodi players on the LAN, send any channel to them and control playback, from a new Integrations page that also hosts the public-address setting and the web-player status; wire "Play on…" into the player dialog and the channel row menu.

**Architecture:** Both media tables (`remote_players`, `media_servers`) land in one Alembic revision here (plan 4 fills the media-server table). Drivers (`VlcDriver`, `KodiDriver`) are sync `httpx.Client` adapters behind a `PlayerDriver` protocol; `RemotePlayerService` owns CRUD, probing (with the secret rule), status, play (stream URL resolution through the base-URL pattern or the `/tuner/stream/<id>.ts` relay), commands and the LAN guard; `scan.py` is an asyncio TCP connect-scan with private-CIDR validation. Endpoints follow the `base_urls.py` CRUD template plus action routes. The frontend gains `remotePlayerService`/hooks, `RemotePlayersSection` (cards, add/edit dialog with Test connection, Find players), `ChannelPickerDialog`, `PlayOnMenu`, and the `Integrations` page skeleton (Public address, Web player, Remote players sections; plan 4 appends Media servers).

**Tech Stack:** SQLAlchemy 2 + Alembic, httpx (`MockTransport` in tests), asyncio; React 18 + MUI + react-query v5; Jest/RTL; Playwright page objects.

**Spec:** `docs/superpowers/specs/2026-09-03-media-integrations-design.md` sections 4.4 (LAN guard, error mapping), 6, 8. Plans 1 and 2 must be complete (they provide `validate_lan_target`, `resolve_public_base_url`, `PlaylistService._stream_link`, `usePublicUrl`, `buildPublicUrl`, `StreamPlayerDialog` with `extraActions`, `ChannelActionHandlers.onPlay`, `usePlayerCapabilities`, `playerService`).

## Global Constraints

- Backend tests: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/<file>`; use `alembic_client`/`alembic_db_session` for anything touching the new tables (they come from the migration).
- HTTP 401 is reserved for the API token. Driver failures: `PlayerUnreachable` → 502 `REMOTE_PLAYER_UNREACHABLE`; `PlayerAuthError(kind)` → 502 `REMOTE_PLAYER_AUTH` with `context.kind` in {`no_password`, `wrong_password`}; `PlayerCommandError` → 400 `REMOTE_PLAYER_COMMAND_FAILED`; forbidden host → 422 `REMOTE_PLAYER_HOST_FORBIDDEN`; scan → 422 `SCAN_CIDR_NOT_PRIVATE` / `SCAN_TOO_LARGE`.
- Driver HTTP clients: `httpx.Client(follow_redirects=False, timeout=httpx.Timeout(5.0, connect=2.0))`; `validate_lan_target(host, resolve=True)` immediately before every outbound request.
- VLC volume is sent on VLC's raw scale: `val = clamp(round(pct * 256 / 100), 0, 512)`; status `volume_pct = round(volume * 100 / 256)`. Never send `N%`. VLC's HTML "Error loading" page (HTTP 200, `text/html`) is a `PlayerCommandError`. No seek command.
- Scan: `cidr` must be inside `10.0.0.0/8, 100.64.0.0/10, 172.16.0.0/12, 192.168.0.0/16, fc00::/7`, `num_addresses <= 1024`, ports 1-65535, at most 8; ≤ 128 concurrent connects, 30 s budget.
- Passwords/API keys are never returned (`has_password`/`has_api_key`) and never logged.
- Frontend: TypeScript only, named prop interfaces, no `any`; `npm run lint -- --max-warnings=0`; `npm run typecheck`; row/card actions keep at most two visible icon buttons, the rest in `RowActionsMenu`; `useConfirm` for deletes; plain-language copy. Nav labels list (routes.test.tsx) becomes `['Overview','Scraper','Search','Acestream Channels','TV Channels','EPG','Playlist','Integrations','Settings']`.
- OpenAPI dump + `npm run codegen` after DTO changes (Task 7). Commit trailers: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_01NCvyzQfF1uXiozTEGgDvPM`. Branch `feature/media-integrations`. Never commit `docs/superpowers/` or `.superpowers/`.

---

### Task 1: Models and the `20260903_1200_add_media_integrations` revision

**Files:**
- Modify: `backend/app/models/models.py` (append two models)
- Create: `backend/migrations/versions/20260903_1200_add_media_integrations.py`
- Test: `backend/tests/test_schema_parity.py`

**Interfaces:**
- Produces ORM classes `RemotePlayer` (`id, name, kind, host, port, username, password, base_url_id, created_at, updated_at`) and `MediaServer` (`id, kind, name, base_url, api_key, tuner_mode, enabled, auto_refresh, tuner_host_id, listing_provider_id, dvr_key, last_lineup_fingerprint, last_guide_fingerprint, last_sync_at, last_sync_status, last_error, server_version, created_at, updated_at`).

- [ ] **Step 1: Write the failing parity test**

Append to `backend/tests/test_schema_parity.py`:

```python
def test_media_integration_tables_match_models(tmp_path):
    engine, inspector = _migrated_inspector(tmp_path, 'media-integrations-parity.db')
    try:
        players = _column_map(inspector, 'remote_players')
        assert set(players) == {'id', 'name', 'kind', 'host', 'port', 'username', 'password', 'base_url_id', 'created_at', 'updated_at'}
        assert players['name']['nullable'] is False and players['port']['nullable'] is False
        assert any(c.get('column_names') == ['name'] for c in inspector.get_unique_constraints('remote_players')) or \
            _has_single_column_index(inspector.get_indexes('remote_players'), 'name', unique=True)
        assert any(fk.get('constrained_columns') == ['base_url_id'] and fk.get('referred_table') == 'base_urls'
                   for fk in inspector.get_foreign_keys('remote_players'))

        servers = _column_map(inspector, 'media_servers')
        assert set(servers) == {
            'id', 'kind', 'name', 'base_url', 'api_key', 'tuner_mode', 'enabled', 'auto_refresh', 'tuner_host_id',
            'listing_provider_id', 'dvr_key', 'last_lineup_fingerprint', 'last_guide_fingerprint', 'last_sync_at',
            'last_sync_status', 'last_error', 'server_version', 'created_at', 'updated_at',
        }
        assert servers['tuner_mode']['nullable'] is False and servers['last_sync_status']['nullable'] is False
    finally:
        engine.dispose()
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_schema_parity.py -k media_integration`
Expected: FAIL (`NoSuchTableError`).

- [ ] **Step 3: Models**

Append to `backend/app/models/models.py` (after `BaseUrl`):

```python
class RemotePlayer(Base):
    """A VLC or Kodi player on the LAN the app can send channels to (spec 6.1)."""
    __tablename__ = "remote_players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    kind = Column(String(16), nullable=False)  # vlc | kodi
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=8080)
    username = Column(String(255), nullable=True)
    password = Column(String(1024), nullable=True)  # never returned by the API
    # null = hand the player the backend relay URL (/tuner/stream/<id>.ts)
    base_url_id = Column(Integer, ForeignKey("base_urls.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(UtcDateTime(), default=_utcnow, nullable=False)
    updated_at = Column(UtcDateTime(), default=_utcnow, onupdate=_utcnow, nullable=False)

    base_url = relationship("BaseUrl")


class MediaServer(Base):
    """A Jellyfin or Plex server kept in sync with the TV channels (spec 7.3)."""
    __tablename__ = "media_servers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(16), nullable=False)  # jellyfin | plex
    name = Column(String(255), unique=True, nullable=False)
    base_url = Column(String(1024), nullable=False)
    api_key = Column(Text, nullable=True)  # Jellyfin API key or Plex owner token; never returned
    tuner_mode = Column(String(16), nullable=False, default="hdhomerun")  # hdhomerun | m3u (Jellyfin only)
    enabled = Column(Boolean, nullable=False, default=True)
    auto_refresh = Column(Boolean, nullable=False, default=True)
    tuner_host_id = Column(String(64), nullable=True)
    listing_provider_id = Column(String(64), nullable=True)
    dvr_key = Column(String(64), nullable=True)
    last_lineup_fingerprint = Column(String(64), nullable=True)
    last_guide_fingerprint = Column(String(64), nullable=True)
    last_sync_at = Column(UtcDateTime(), nullable=True)
    last_sync_status = Column(String(16), nullable=False, default="never")  # ok | error | never | manual
    last_error = Column(Text, nullable=True)
    server_version = Column(String(64), nullable=True)
    created_at = Column(UtcDateTime(), default=_utcnow, nullable=False)
    updated_at = Column(UtcDateTime(), default=_utcnow, onupdate=_utcnow, nullable=False)
```

- [ ] **Step 4: Migration**

Create `backend/migrations/versions/20260903_1200_add_media_integrations.py`:

```python
"""
Media integrations (spec 6.1, 7.3): remote_players (VLC/Kodi targets) and
media_servers (Jellyfin/Plex sync state). Idempotent for databases that were
provisioned by create_all and stamped afterwards.
"""
from alembic import op
import sqlalchemy as sa


revision = '20260903_1200'
down_revision = '20260824_1200'
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table('remote_players'):
        op.create_table(
            'remote_players',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('name', sa.String(length=255), nullable=False, unique=True),
            sa.Column('kind', sa.String(length=16), nullable=False),
            sa.Column('host', sa.String(length=255), nullable=False),
            sa.Column('port', sa.Integer(), nullable=False, server_default='8080'),
            sa.Column('username', sa.String(length=255), nullable=True),
            sa.Column('password', sa.String(length=1024), nullable=True),
            sa.Column('base_url_id', sa.Integer(), sa.ForeignKey('base_urls.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
    if not _has_table('media_servers'):
        op.create_table(
            'media_servers',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('kind', sa.String(length=16), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False, unique=True),
            sa.Column('base_url', sa.String(length=1024), nullable=False),
            sa.Column('api_key', sa.Text(), nullable=True),
            sa.Column('tuner_mode', sa.String(length=16), nullable=False, server_default='hdhomerun'),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('auto_refresh', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('tuner_host_id', sa.String(length=64), nullable=True),
            sa.Column('listing_provider_id', sa.String(length=64), nullable=True),
            sa.Column('dvr_key', sa.String(length=64), nullable=True),
            sa.Column('last_lineup_fingerprint', sa.String(length=64), nullable=True),
            sa.Column('last_guide_fingerprint', sa.String(length=64), nullable=True),
            sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_sync_status', sa.String(length=16), nullable=False, server_default='never'),
            sa.Column('last_error', sa.Text(), nullable=True),
            sa.Column('server_version', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    if _has_table('media_servers'):
        op.drop_table('media_servers')
    if _has_table('remote_players'):
        op.drop_table('remote_players')
```

- [ ] **Step 5: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_schema_parity.py backend/tests/test_startup_db_init.py && PYTHONPATH=backend alembic -c backend/migrations/alembic.ini history | head -3`
Expected: PASS; history shows `20260824_1200 -> 20260903_1200 (head)`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/models.py backend/migrations/versions/20260903_1200_add_media_integrations.py backend/tests/test_schema_parity.py
git commit -m "feat(db): remote_players and media_servers tables"
```

---

### Task 2: Player drivers (VLC, Kodi)

**Files:**
- Create: `backend/app/services/remote_players/__init__.py`, `backend/app/services/remote_players/base.py`, `backend/app/services/remote_players/vlc.py`, `backend/app/services/remote_players/kodi.py`
- Test: `backend/tests/test_remote_player_drivers.py`

**Interfaces:**
- Produces (in `base.py`): `PlayerUnreachable(RuntimeError)`, `PlayerAuthError(RuntimeError)` with `.kind: Literal["no_password","wrong_password"]`, `PlayerCommandError(RuntimeError)`; `@dataclass PlayerProbe(reachable: bool, authenticated: bool, version: str|None, message: str, hint: str|None)`; `@dataclass PlayerStatus(state: Literal["playing","paused","stopped"], title: str|None, position_s: int|None, length_s: int|None, volume_pct: int|None, message: str|None)`; `PlayerDriver` protocol with `probe() -> PlayerProbe`, `status() -> PlayerStatus`, `play(url: str, title: str) -> None`, `pause()`, `resume()`, `stop()`, `set_volume(pct: int)`; `new_client() -> httpx.Client`; `guard(host: str) -> None` (calls `validate_lan_target(host, resolve=True)`, raising `PlayerUnreachable`).
- `VlcDriver(host, port, password, client=None)`, `KodiDriver(host, port, username, password, client=None)`, `make_driver(kind, host, port, username, password, client=None)`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_remote_player_drivers.py`:

```python
"""VLC HTTP interface and Kodi JSON-RPC drivers (spec 6.2)."""
import json

import httpx
import pytest

from app.services.remote_players.base import PlayerAuthError, PlayerCommandError, PlayerUnreachable
from app.services.remote_players.kodi import KodiDriver
from app.services.remote_players.vlc import VlcDriver

STATUS = {"apiversion": 3, "version": "3.0.23", "state": "playing", "time": 61, "length": 0, "volume": 256,
          "information": {"category": {"meta": {"title": "Arena TV", "filename": "stream.ts"}}}}


def _vlc(handler):
    return VlcDriver("192.168.1.20", 8080, "pw", client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_vlc_status_and_volume_scale():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=STATUS, headers={"Content-Type": "application/json"})

    status = _vlc(handler).status()
    assert seen[0].url.path == "/requests/status.json"
    assert seen[0].headers["Authorization"].startswith("Basic ")  # ("", "pw")
    assert (status.state, status.title, status.position_s, status.volume_pct) == ("playing", "Arena TV", 61, 100)


def test_vlc_play_clears_playlist_then_in_play_with_encoded_url():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json=STATUS)

    _vlc(handler).play("http://scraper.lan:8000/tuner/stream/abc.ts?x=1&y=2", "Arena TV")
    assert seen[0].endswith("/requests/status.json?command=pl_empty")
    assert "command=in_play&input=http%3A%2F%2Fscraper.lan%3A8000%2Ftuner%2Fstream%2Fabc.ts%3Fx%3D1%26y%3D2" in seen[1]


@pytest.mark.parametrize(("pct", "expected"), [(0, 0), (50, 128), (100, 256), (200, 512), (250, 512)])
def test_vlc_volume_uses_raw_scale(pct, expected):
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json=STATUS)

    _vlc(handler).set_volume(pct)
    assert seen[0] == {"command": "volume", "val": str(expected)}


def test_vlc_pause_resume_stop_commands():
    seen = []

    def handler(request):
        seen.append(request.url.params["command"])
        return httpx.Response(200, json=STATUS)

    driver = _vlc(handler)
    driver.pause(); driver.resume(); driver.stop()
    assert seen == ["pl_forcepause", "pl_forceresume", "pl_stop"]


def test_vlc_auth_errors_are_distinct():
    with pytest.raises(PlayerAuthError) as no_pw:
        _vlc(lambda r: httpx.Response(403, text="no password")).status()
    assert no_pw.value.kind == "no_password"
    with pytest.raises(PlayerAuthError) as wrong:
        _vlc(lambda r: httpx.Response(401, text="unauthorized")).status()
    assert wrong.value.kind == "wrong_password"


def test_vlc_html_error_page_is_a_command_error():
    html = "<html><body><h1>Error loading status.json</h1><pre>lua: bad argument #1 to 'set' (number expected)</pre></body></html>"
    with pytest.raises(PlayerCommandError, match="number expected"):
        _vlc(lambda r: httpx.Response(200, text=html, headers={"Content-Type": "text/html"})).set_volume(50)


def test_vlc_connection_error_is_unreachable():
    def handler(request):
        raise httpx.ConnectError("refused")
    with pytest.raises(PlayerUnreachable):
        _vlc(handler).probe()


def test_vlc_probe_reports_version():
    probe = _vlc(lambda r: httpx.Response(200, json=STATUS)).probe()
    assert probe.reachable and probe.authenticated and probe.version == "3.0.23"
    probe = _vlc(lambda r: httpx.Response(403)).probe()
    assert probe.reachable and not probe.authenticated and "password" in probe.hint.lower()


def test_drivers_refuse_forbidden_hosts(monkeypatch):
    driver = VlcDriver("169.254.169.254", 8080, "pw", client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=STATUS))))
    with pytest.raises(PlayerUnreachable, match="metadata"):
        driver.status()


def _kodi(handler):
    return KodiDriver("192.168.1.30", 8080, "kodi", "pw", client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_kodi_play_and_commands():
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append((body["method"], body.get("params")))
        if body["method"] == "Player.GetActivePlayers":
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": [{"playerid": 1, "type": "video"}]})
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": "OK"})

    driver = _kodi(handler)
    driver.play("http://x/stream.ts", "Arena TV")
    driver.pause(); driver.resume(); driver.stop(); driver.set_volume(150)
    methods = [m for m, _ in calls]
    assert methods[0] == "Player.Open" and calls[0][1] == {"item": {"file": "http://x/stream.ts"}}
    assert ("Player.PlayPause", {"playerid": 1, "play": False}) in calls
    assert ("Player.PlayPause", {"playerid": 1, "play": True}) in calls
    assert ("Player.Stop", {"playerid": 1}) in calls
    assert ("Application.SetVolume", {"volume": 100}) in calls  # clamped to 100


def test_kodi_status():
    def handler(request):
        method = json.loads(request.content)["method"]
        results = {
            "Player.GetActivePlayers": [{"playerid": 1, "type": "video"}],
            "Player.GetProperties": {"time": {"hours": 0, "minutes": 1, "seconds": 5, "milliseconds": 0}, "totaltime": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 0}, "speed": 0},
            "Player.GetItem": {"item": {"title": "Arena TV", "file": "http://x"}},
            "Application.GetProperties": {"volume": 80, "version": {"major": 21, "minor": 1}},
        }
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": results[method]})

    status = _kodi(handler).status()
    assert (status.state, status.title, status.position_s, status.volume_pct) == ("paused", "Arena TV", 65, 80)


def test_kodi_idle_is_stopped_and_auth_maps():
    def idle(request):
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": []})
    assert _kodi(idle).status().state == "stopped"
    with pytest.raises(PlayerAuthError) as exc:
        _kodi(lambda r: httpx.Response(401)).status()
    assert exc.value.kind == "wrong_password"
    with pytest.raises(PlayerCommandError, match="not found"):
        _kodi(lambda r: httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}})).stop()
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_remote_player_drivers.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

`backend/app/services/remote_players/__init__.py`: empty.

`backend/app/services/remote_players/base.py`:

```python
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
```

`backend/app/services/remote_players/vlc.py`:

```python
"""VLC Lua HTTP interface driver (VLC 3.x/4.x desktop)."""
from __future__ import annotations

import re
from typing import Optional

import httpx

from .base import PlayerAuthError, PlayerCommandError, PlayerProbe, PlayerStatus, PlayerUnreachable, guard, new_client

VLC_MAX_VOLUME = 512  # 256 = 100 %, 512 = VLC's 200 % GUI ceiling
NO_PASSWORD_HINT = ("VLC's web interface has no password. In VLC: Tools > Preferences > All > Interface > "
                    "Main interfaces > Web, then Lua > Lua HTTP > Password.")
WRONG_PASSWORD_HINT = "Check the password (VLC: Lua HTTP password)."
_PRE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.S | re.I)


class VlcDriver:
    def __init__(self, host: str, port: int, password: Optional[str], client: Optional[httpx.Client] = None):
        self.host = host
        self.port = int(port)
        self.password = password or ""
        self._client = client or new_client()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _request(self, command: Optional[str] = None, **params) -> dict:
        guard(self.host)
        query = {}
        if command:
            query["command"] = command
        query.update({k: v for k, v in params.items() if v is not None})
        try:
            response = self._client.get(f"{self.base_url}/requests/status.json", params=query, auth=("", self.password))
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
            raise PlayerCommandError((match.group(1).strip() if match else "VLC reported an error").replace("\n", " ")[:300])
        try:
            return response.json()
        except ValueError as exc:
            raise PlayerCommandError("VLC returned a non-JSON status") from exc

    def probe(self) -> PlayerProbe:
        try:
            status = self._request()
        except PlayerAuthError as exc:
            return PlayerProbe(reachable=True, authenticated=False, version=None, message=str(exc), hint=str(exc))
        return PlayerProbe(reachable=True, authenticated=True, version=status.get("version"), message="VLC is reachable")

    def status(self) -> PlayerStatus:
        data = self._request()
        meta = (((data.get("information") or {}).get("category") or {}).get("meta") or {})
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
```

`backend/app/services/remote_players/kodi.py`:

```python
"""Kodi JSON-RPC (HTTP) driver."""
from __future__ import annotations

from typing import Any, Optional

import httpx

from .base import PlayerAuthError, PlayerCommandError, PlayerProbe, PlayerStatus, PlayerUnreachable, guard, new_client

WRONG_PASSWORD_HINT = "Check the Kodi username and password (Settings > Services > Control)."


class KodiDriver:
    def __init__(self, host: str, port: int, username: Optional[str], password: Optional[str], client: Optional[httpx.Client] = None):
        self.host = host
        self.port = int(port)
        self.username = username or "kodi"
        self.password = password or ""
        self._client = client or new_client()

    def _rpc(self, method: str, params: Optional[dict] = None) -> Any:
        guard(self.host)
        payload = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            payload["params"] = params
        try:
            response = self._client.post(f"http://{self.host}:{self.port}/jsonrpc", json=payload, auth=(self.username, self.password))
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
            return PlayerProbe(reachable=True, authenticated=False, version=None, message=str(exc), hint=str(exc))
        version = props.get("version") or {}
        version_text = f"{version.get('major')}.{version.get('minor')}" if version else None
        return PlayerProbe(reachable=True, authenticated=True, version=version_text, message="Kodi is reachable")

    def status(self) -> PlayerStatus:
        player_id = self._active_player_id()
        app = self._rpc("Application.GetProperties", {"properties": ["volume"]}) or {}
        volume = app.get("volume")
        if player_id is None:
            return PlayerStatus(state="stopped", volume_pct=volume)
        props = self._rpc("Player.GetProperties", {"playerid": player_id, "properties": ["time", "totaltime", "speed"]}) or {}
        item = (self._rpc("Player.GetItem", {"playerid": player_id, "properties": ["title", "file"]}) or {}).get("item") or {}
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
    return int(value.get("hours", 0)) * 3600 + int(value.get("minutes", 0)) * 60 + int(value.get("seconds", 0))
```

Add to `base.py` (bottom) a factory used by the service and tests:

```python
def make_driver(kind: str, host: str, port: int, username: Optional[str], password: Optional[str], client: Optional[httpx.Client] = None) -> PlayerDriver:
    if kind == "vlc":
        from .vlc import VlcDriver
        return VlcDriver(host, port, password, client=client)
    if kind == "kodi":
        from .kodi import KodiDriver
        return KodiDriver(host, port, username, password, client=client)
    raise ValueError(f"unknown player kind: {kind}")
```

- [ ] **Step 4: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_remote_player_drivers.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/remote_players backend/tests/test_remote_player_drivers.py
git commit -m "feat(remote-players): VLC and Kodi drivers"
```

---

### Task 3: Repository, service (probe/status/play/command, stream URL, LAN guard) and scan

**Files:**
- Create: `backend/app/repositories/remote_player_repository.py`, `backend/app/services/remote_players/service.py`, `backend/app/services/remote_players/scan.py`
- Test: `backend/tests/test_remote_player_service.py`, `backend/tests/test_remote_player_scan.py`

**Interfaces:**
- Produces:
  ```python
  class RemotePlayerRepository(db): get_all() ; get(id) ; get_by_name(name) ; create(**fields) ; update(entry, **fields) ; delete(entry)
  class RemotePlayerService:
      def __init__(self, db, *, client_factory=new_client, settings_getter=get_settings)
      def validate_host(self, host) -> str                       # raises BlockedURLError
      def probe(self, kind, host, port, username, password, stored_id=None) -> tuple[PlayerProbe, TunerAccess]
      def tuner_access(self, host) -> TunerAccess(addresses: list[str], allowed: bool)
      def status(self, player) -> PlayerStatus
      def resolve_stream_url(self, player, content_id, public_base_url) -> str
      def play(self, player, content_id, public_base_url, title) -> str
      def command(self, player, command, value=None) -> None    # pause|resume|stop|volume
  # scan.py
  PRIVATE_SCAN_NETWORKS ; class ScanValidationError(ValueError): code
  def validate_scan_request(cidr: str, ports: list[int]) -> tuple[ip_network, list[int]]
  async def scan_network(network, ports, timeout_ms=400, concurrency=128, budget_s=30.0, client_factory=None) -> ScanOutcome(hits: list[ScanHit], scanned: int, duration_ms: int)
  def default_scan_cidr(client_ip: str|None) -> str|None
  ```

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_remote_player_service.py`:

```python
import httpx
import pytest

from app.services.remote_players.base import PlayerAuthError
from app.services.remote_players.service import RemotePlayerService
from app.utils.url_guard import BlockedURLError

VLC_OK = {"apiversion": 3, "version": "3.0.23", "state": "stopped", "time": 0, "length": 0, "volume": 256, "information": {}}
IH = "0" * 40


def _service(db, handler=None):
    def factory():
        return httpx.Client(transport=httpx.MockTransport(handler or (lambda r: httpx.Response(200, json=VLC_OK))))
    return RemotePlayerService(db, client_factory=factory)


def test_crud_and_password_masking(alembic_db_session):
    svc = _service(alembic_db_session)
    player = svc.repo.create(name="Living room", kind="vlc", host="192.168.1.20", port=8080, username=None, password="pw", base_url_id=None)
    assert svc.repo.get_by_name("Living room").id == player.id
    svc.repo.update(player, name="Lounge", password=None)  # None = keep
    assert svc.repo.get(player.id).password == "pw" and svc.repo.get(player.id).name == "Lounge"
    svc.repo.update(player, password="")  # empty = clear
    assert svc.repo.get(player.id).password == ""
    svc.repo.delete(player)
    assert svc.repo.get_all() == []


def test_validate_host_rules(alembic_db_session):
    svc = _service(alembic_db_session)
    assert svc.validate_host(" vlc.lan ") == "vlc.lan"
    assert svc.validate_host("192.168.1.5") == "192.168.1.5"
    for bad in ("http://x", "user@host", "host/path", "", "169.254.169.254"):
        with pytest.raises((BlockedURLError, ValueError)):
            svc.validate_host(bad)


def test_probe_secret_rule(alembic_db_session):
    seen = []

    def handler(request):
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=VLC_OK)

    svc = _service(alembic_db_session, handler)
    stored = svc.repo.create(name="p", kind="vlc", host="192.168.1.20", port=8080, username=None, password="stored", base_url_id=None)
    svc.probe("vlc", "192.168.1.20", 8080, None, "typed", stored_id=stored.id)
    svc.probe("vlc", "192.168.1.20", 8080, None, "", stored_id=stored.id)
    svc.probe("vlc", "192.168.1.20", 8080, None, None, stored_id=None)
    import base64
    assert seen[0] == "Basic " + base64.b64encode(b":typed").decode()
    assert seen[1] == "Basic " + base64.b64encode(b":stored").decode()
    assert seen[2] == "Basic " + base64.b64encode(b":").decode()


def test_probe_reports_tuner_access(alembic_db_session, monkeypatch):
    svc = _service(alembic_db_session)
    import socket
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))])
    probe, access = svc.probe("vlc", "public.example", 8080, None, "pw")
    assert probe.reachable
    assert access.addresses == ["8.8.8.8"] and access.allowed is False


def test_resolve_stream_url_relay_and_pattern(alembic_db_session):
    from app.repositories.base_url_repository import BaseUrlRepository
    svc = _service(alembic_db_session)
    pattern = BaseUrlRepository(alembic_db_session).create("Acexy", "http://192.168.1.10:8080/ace/getstream?id={channel_id}&pid={pid}")
    relay = svc.repo.create(name="relay", kind="vlc", host="192.168.1.20", port=8080, username=None, password="pw", base_url_id=None)
    custom = svc.repo.create(name="custom", kind="vlc", host="192.168.1.21", port=8080, username=None, password="pw", base_url_id=pattern.id)
    assert svc.resolve_stream_url(relay, IH, "http://scraper.lan:8000") == f"http://scraper.lan:8000/tuner/stream/{IH}.ts"
    assert svc.resolve_stream_url(custom, IH, "http://scraper.lan:8000") == f"http://192.168.1.10:8080/ace/getstream?id={IH}"


def test_play_and_commands_go_through_the_driver(alembic_db_session):
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json=VLC_OK)

    svc = _service(alembic_db_session, handler)
    player = svc.repo.create(name="p", kind="vlc", host="192.168.1.20", port=8080, username=None, password="pw", base_url_id=None)
    url = svc.play(player, IH, "http://scraper.lan:8000", "Arena")
    assert url.endswith(f"/tuner/stream/{IH}.ts")
    svc.command(player, "volume", 50)
    svc.command(player, "stop")
    assert seen[0]["command"] == "pl_empty" and seen[1]["command"] == "in_play"
    assert seen[2] == {"command": "volume", "val": "128"} and seen[3]["command"] == "pl_stop"
    with pytest.raises(ValueError):
        svc.command(player, "seek", 10)


def test_status_propagates_auth_error(alembic_db_session):
    svc = _service(alembic_db_session, lambda r: httpx.Response(401))
    player = svc.repo.create(name="p", kind="vlc", host="192.168.1.20", port=8080, username=None, password="bad", base_url_id=None)
    with pytest.raises(PlayerAuthError):
        svc.status(player)
```

Create `backend/tests/test_remote_player_scan.py`:

```python
import asyncio
import ipaddress
import socket

import httpx
import pytest

from app.services.remote_players.scan import ScanValidationError, default_scan_cidr, scan_network, validate_scan_request


@pytest.mark.parametrize(("cidr", "code"), [
    ("8.8.8.0/22", "SCAN_CIDR_NOT_PRIVATE"), ("169.254.0.0/22", "SCAN_CIDR_NOT_PRIVATE"), ("127.0.0.0/24", "SCAN_CIDR_NOT_PRIVATE"),
    ("fd00::/22", "SCAN_TOO_LARGE"), ("10.0.0.0/8", "SCAN_TOO_LARGE"),
])
def test_validate_scan_request_rejects(cidr, code):
    with pytest.raises(ScanValidationError) as exc:
        validate_scan_request(cidr, [8080])
    assert exc.value.code == code


def test_validate_scan_request_accepts_private_and_normalises():
    network, ports = validate_scan_request("192.168.1.77/24", [8080, 8080, 80])
    assert str(network) == "192.168.1.0/24" and ports == [8080, 80]
    with pytest.raises(ScanValidationError, match="ports"):
        validate_scan_request("192.168.1.0/24", [0])
    with pytest.raises(ScanValidationError, match="ports"):
        validate_scan_request("192.168.1.0/24", list(range(1, 10)))


@pytest.mark.parametrize(("client_ip", "expected"), [
    ("192.168.1.55", "192.168.1.0/24"), ("10.2.3.4", "10.2.3.0/24"), ("100.64.1.9", "100.64.1.0/24"),
    ("172.17.0.1", None), ("192.168.65.1", None), ("127.0.0.1", None), ("203.0.113.5", None), ("testclient", None), (None, None),
])
def test_default_scan_cidr(client_ip, expected):
    assert default_scan_cidr(client_ip) == expected


def test_scan_classifies_vlc_and_kodi_on_a_local_server():
    async def run():
        async def vlc_handler(reader, writer):
            await reader.read(1024)
            writer.write(b"HTTP/1.0 403 Forbidden\r\nContent-Type: text/html\r\nContent-Length: 0\r\n\r\n")
            await writer.drain(); writer.close()

        async def kodi_handler(reader, writer):
            await reader.read(1024)
            writer.write(b"HTTP/1.0 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Kodi\"\r\nContent-Length: 0\r\n\r\n")
            await writer.drain(); writer.close()

        vlc = await asyncio.start_server(vlc_handler, "127.0.0.1", 0)
        kodi = await asyncio.start_server(kodi_handler, "127.0.0.1", 0)
        vlc_port = vlc.sockets[0].getsockname()[1]
        kodi_port = kodi.sockets[0].getsockname()[1]
        try:
            outcome = await scan_network(ipaddress.ip_network("127.0.0.1/32"), [vlc_port, kodi_port, 1], timeout_ms=500)
        finally:
            vlc.close(); kodi.close()
        kinds = {(h.host, h.port): h.kind for h in outcome.hits}
        assert kinds[("127.0.0.1", vlc_port)] == "vlc"
        assert kinds[("127.0.0.1", kodi_port)] == "kodi"
        assert ("127.0.0.1", 1) not in kinds
        assert outcome.scanned == 3
    asyncio.run(run())
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_remote_player_service.py backend/tests/test_remote_player_scan.py`
Expected: FAIL.

- [ ] **Step 3: Repository**

Create `backend/app/repositories/remote_player_repository.py`:

```python
"""DB access for remote players (spec 6.1)."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import RemotePlayer

_KEEP = object()


class RemotePlayerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[RemotePlayer]:
        return self.db.query(RemotePlayer).order_by(RemotePlayer.name).all()

    def get(self, player_id: int) -> Optional[RemotePlayer]:
        return self.db.query(RemotePlayer).filter(RemotePlayer.id == player_id).first()

    def get_by_name(self, name: str) -> Optional[RemotePlayer]:
        return self.db.query(RemotePlayer).filter(RemotePlayer.name == name).first()

    def create(self, *, name: str, kind: str, host: str, port: int, username: Optional[str], password: Optional[str], base_url_id: Optional[int]) -> RemotePlayer:
        entry = RemotePlayer(name=name, kind=kind, host=host, port=port, username=username, password=password, base_url_id=base_url_id)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry: RemotePlayer, *, name=_KEEP, kind=_KEEP, host=_KEEP, port=_KEEP, username=_KEEP, password=_KEEP, base_url_id=_KEEP) -> RemotePlayer:
        """None for password means keep; "" clears it. Other fields: None keeps."""
        for field, value in (("name", name), ("kind", kind), ("host", host), ("port", port), ("username", username), ("base_url_id", base_url_id)):
            if value is not _KEEP and value is not None:
                setattr(entry, field, value)
        if base_url_id is not _KEEP and base_url_id is None and name is _KEEP:
            pass  # explicit clearing goes through clear_base_url()
        if password is not _KEEP and password is not None:
            entry.password = password
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def clear_base_url(self, entry: RemotePlayer) -> RemotePlayer:
        entry.base_url_id = None
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: RemotePlayer) -> None:
        self.db.delete(entry)
        self.db.commit()
```

- [ ] **Step 4: Service**

Create `backend/app/services/remote_players/service.py`:

```python
"""Remote player use cases (spec 6.1, 6.3)."""
from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

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


@dataclass
class TunerAccess:
    addresses: List[str] = field(default_factory=list)
    allowed: bool = True


class RemotePlayerService:
    def __init__(self, db: Session, *, client_factory: Callable[[], httpx.Client] = new_client, settings_getter: Callable = get_settings):
        self.db = db
        self.repo = RemotePlayerRepository(db)
        self._client_factory = client_factory
        self._settings = settings_getter

    # --- validation ------------------------------------------------------------
    def validate_host(self, host: str) -> str:
        candidate = (host or "").strip()
        if not candidate or "/" in candidate or "@" in candidate or "://" in candidate or " " in candidate:
            raise ValueError("host must be a hostname or IP address without scheme, credentials or path")
        validate_lan_target(candidate, resolve=False)
        return candidate

    def tuner_access(self, host: str) -> TunerAccess:
        gate = TunerNetworkGate(self._settings().TUNER_ALLOWED_NETWORKS)
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            return TunerAccess(addresses=[], allowed=True)
        addresses = sorted({info[4][0] for info in infos})
        return TunerAccess(addresses=addresses, allowed=all(gate.is_allowed(a) for a in addresses))

    # --- drivers ---------------------------------------------------------------
    def _driver(self, kind: str, host: str, port: int, username: Optional[str], password: Optional[str]) -> PlayerDriver:
        return make_driver(kind, host, port, username, password, client=self._client_factory())

    def driver_for(self, player: RemotePlayer) -> PlayerDriver:
        return self._driver(player.kind, player.host, player.port, player.username, player.password)

    def probe(self, kind: str, host: str, port: int, username: Optional[str], password: Optional[str], stored_id: Optional[int] = None) -> Tuple[PlayerProbe, TunerAccess]:
        """Secret rule: body password when non-empty; else the stored one when stored_id is given; else none."""
        secret = password if password else None
        if secret is None and stored_id is not None:
            stored = self.repo.get(stored_id)
            if stored is not None:
                secret = stored.password
        driver = self._driver(kind, host, port, username, secret or "")
        return driver.probe(), self.tuner_access(host)

    def status(self, player: RemotePlayer) -> PlayerStatus:
        return self.driver_for(player).status()

    def resolve_stream_url(self, player: RemotePlayer, content_id: str, public_base_url: str) -> str:
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
            driver.set_volume(max(0, min(200, int(value))))
```

- [ ] **Step 5: Scan**

Create `backend/app/services/remote_players/scan.py`:

```python
"""Find VLC/Kodi web interfaces on a private network (spec 6.1)."""
from __future__ import annotations

import asyncio
import ipaddress
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import httpx

PRIVATE_SCAN_NETWORKS = tuple(ipaddress.ip_network(n) for n in ("10.0.0.0/8", "100.64.0.0/10", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7"))
MAX_ADDRESSES = 1024
MAX_PORTS = 8
_DOCKER_DESKTOP = ipaddress.ip_network("192.168.65.0/24")
_DOCKER_BRIDGE = ipaddress.ip_network("172.16.0.0/12")


class ScanValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class ScanHit:
    host: str
    port: int
    kind: str  # vlc | kodi | unknown
    hint: str


@dataclass
class ScanOutcome:
    hits: List[ScanHit] = field(default_factory=list)
    scanned: int = 0
    duration_ms: int = 0


def validate_scan_request(cidr: str, ports: List[int]):
    try:
        network = ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError as exc:
        raise ScanValidationError("SCAN_CIDR_NOT_PRIVATE", f"{cidr!r} is not a valid network") from exc
    if not any(network.subnet_of(private) for private in PRIVATE_SCAN_NETWORKS if private.version == network.version):
        raise ScanValidationError("SCAN_CIDR_NOT_PRIVATE", "Only private networks can be scanned (10/8, 100.64/10, 172.16/12, 192.168/16, fc00::/7)")
    if network.num_addresses > MAX_ADDRESSES:
        raise ScanValidationError("SCAN_TOO_LARGE", f"Scan at most {MAX_ADDRESSES} addresses at a time (a /22 or smaller)")
    unique_ports = list(dict.fromkeys(int(p) for p in ports))
    if not unique_ports or len(unique_ports) > MAX_PORTS or any(p < 1 or p > 65535 for p in unique_ports):
        raise ScanValidationError("SCAN_TOO_LARGE", f"ports must be 1-65535, at most {MAX_PORTS}")
    return network, unique_ports


def default_scan_cidr(client_ip: Optional[str]) -> Optional[str]:
    try:
        address = ipaddress.ip_address((client_ip or "").strip("[]"))
    except ValueError:
        return None
    mapped = getattr(address, "ipv4_mapped", None)
    address = mapped if mapped is not None else address
    if address.version != 4 or address.is_loopback or address in _DOCKER_DESKTOP:
        return None
    if address in _DOCKER_BRIDGE and str(address).endswith(".1"):
        return None
    if not any(address in n for n in PRIVATE_SCAN_NETWORKS if n.version == 4):
        return None
    return str(ipaddress.ip_network(f"{address}/24", strict=False))


async def _tcp_open(host: str, port: int, timeout: float) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
    except (OSError, asyncio.TimeoutError):
        return False
    writer.close()
    return True


def classify(host: str, port: int, client: httpx.Client) -> ScanHit:
    base = f"http://{host}:{port}"
    try:
        r = client.get(f"{base}/requests/status.json")
        if r.status_code in (401, 403) and "kodi" not in r.headers.get("WWW-Authenticate", "").lower() or (r.status_code == 200 and "apiversion" in r.text):
            hint = "web interface has no password" if r.status_code == 403 else "password required" if r.status_code == 401 else "open"
            return ScanHit(host=host, port=port, kind="vlc", hint=hint)
    except httpx.HTTPError:
        pass
    try:
        r = client.post(f"{base}/jsonrpc", json={"jsonrpc": "2.0", "id": 1, "method": "JSONRPC.Ping"})
        if r.status_code == 401 or (r.status_code == 200 and '"pong"' in r.text):
            return ScanHit(host=host, port=port, kind="kodi", hint="password required" if r.status_code == 401 else "open")
    except httpx.HTTPError:
        pass
    return ScanHit(host=host, port=port, kind="unknown", hint="something answers on this port")


async def scan_network(network, ports: List[int], timeout_ms: int = 400, concurrency: int = 128, budget_s: float = 30.0,
                       client_factory: Optional[Callable[[], httpx.Client]] = None) -> ScanOutcome:
    started = time.monotonic()
    semaphore = asyncio.Semaphore(concurrency)
    timeout = max(0.05, timeout_ms / 1000)
    hosts = [str(a) for a in (network.hosts() if network.num_addresses > 2 else [network.network_address])]
    outcome = ScanOutcome()

    async def check(host: str, port: int):
        if time.monotonic() - started > budget_s:
            return None
        async with semaphore:
            outcome.scanned += 1
            return (host, port) if await _tcp_open(host, port, timeout) else None

    results = await asyncio.gather(*(check(h, p) for h in hosts for p in ports))
    open_ports = [r for r in results if r]
    factory = client_factory or (lambda: httpx.Client(follow_redirects=False, timeout=httpx.Timeout(2.0, connect=1.0)))
    if open_ports:
        with factory() as client:
            outcome.hits = await asyncio.gather(*(asyncio.to_thread(classify, h, p, client) for h, p in open_ports))
    outcome.duration_ms = int((time.monotonic() - started) * 1000)
    return outcome
```

The Kodi detection in `classify` must not be confused by VLC's 401: VLC answers 401/403 on `/requests/status.json`, Kodi answers 404 there and 401 on `/jsonrpc`. If the local-server test's VLC stub (403 on any path) gets classified as vlc before the jsonrpc probe, the order above is right; make sure the `WWW-Authenticate: Basic realm="Kodi"` header on the Kodi stub keeps it out of the vlc branch (the condition checks the realm).

- [ ] **Step 6: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_remote_player_service.py backend/tests/test_remote_player_scan.py`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/repositories/remote_player_repository.py backend/app/services/remote_players/service.py backend/app/services/remote_players/scan.py backend/tests/test_remote_player_service.py backend/tests/test_remote_player_scan.py
git commit -m "feat(remote-players): service, repository, LAN guard and network scan"
```

---

### Task 4: Remote player endpoints and DTOs

**Files:**
- Create: `backend/app/schemas/remote_players.py`, `backend/app/api/endpoints/remote_players.py`
- Modify: `backend/app/api/api.py`
- Test: `backend/tests/test_remote_players_api.py`

**Interfaces:**
- Produces `/api/v1/remote-players`: `GET ""` → `List[RemotePlayerResponse]`; `POST ""` 201; `PATCH /{id}`; `DELETE /{id}` 204; `POST /test` (`RemotePlayerTestRequest` → `RemotePlayerProbeResponse`); `POST /{id}/test`; `GET /{id}/status` → `RemotePlayerStatusResponse`; `POST /{id}/play` (`RemotePlayerPlayRequest{content_id, title?}` → 202 `RemotePlayerPlayResponse{url}`); `POST /{id}/command` (`RemotePlayerCommandRequest{command, value?}` → 204); `POST /scan` (`ScanRequest` → `ScanResultResponse`); `GET /scan/default` → `ScanDefaultResponse{cidr, hint}`.
- DTO names: `RemotePlayerCreate`, `RemotePlayerUpdate`, `RemotePlayerResponse`, `RemotePlayerTestRequest`, `TunerAccessResponse`, `RemotePlayerProbeResponse`, `RemotePlayerStatusResponse`, `RemotePlayerPlayRequest`, `RemotePlayerPlayResponse`, `RemotePlayerCommandRequest`, `ScanRequest`, `ScanHitResponse`, `ScanResultResponse`, `ScanDefaultResponse`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_remote_players_api.py`:

```python
import httpx
import pytest

VLC_OK = {"apiversion": 3, "version": "3.0.23", "state": "playing", "time": 5, "length": 0, "volume": 128, "information": {"category": {"meta": {"title": "Arena"}}}}
IH = "0" * 40


@pytest.fixture
def vlc(monkeypatch):
    """Route every driver client through a MockTransport; tests set `vlc.handler`."""
    import app.api.endpoints.remote_players as endpoint
    state = {"handler": lambda r: httpx.Response(200, json=VLC_OK)}

    def factory():
        return httpx.Client(transport=httpx.MockTransport(lambda r: state["handler"](r)))
    monkeypatch.setattr(endpoint, "_client_factory", factory)
    return state


def _create(client, **overrides):
    body = {"name": "Living room", "kind": "vlc", "host": "192.168.1.20", "port": 8080, "password": "pw"}
    body.update(overrides)
    return client.post("/api/v1/remote-players", json=body)


def test_crud_masks_the_password(alembic_client, vlc):
    created = _create(alembic_client)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["has_password"] is True and "password" not in body and body["base_url_id"] is None
    assert _create(alembic_client).status_code == 409
    patched = alembic_client.patch(f"/api/v1/remote-players/{body['id']}", json={"name": "Lounge", "port": 9090})
    assert patched.json()["name"] == "Lounge" and patched.json()["port"] == 9090 and patched.json()["has_password"] is True
    assert alembic_client.get("/api/v1/remote-players").json()[0]["name"] == "Lounge"
    assert alembic_client.delete(f"/api/v1/remote-players/{body['id']}").status_code == 204
    assert alembic_client.get("/api/v1/remote-players").json() == []


def test_forbidden_host_is_422(alembic_client, vlc):
    response = _create(alembic_client, host="169.254.169.254")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REMOTE_PLAYER_HOST_FORBIDDEN"


def test_test_endpoint_without_a_row(alembic_client, vlc):
    probes = []

    def handler(request):
        probes.append(request.headers.get("Authorization"))
        return httpx.Response(403)
    vlc["handler"] = handler
    response = alembic_client.post("/api/v1/remote-players/test", json={"kind": "vlc", "host": "192.168.1.20", "port": 8080})
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] and not body["authenticated"] and "password" in body["hint"].lower()
    assert set(body["tuner_access"]) == {"addresses", "allowed"}
    assert alembic_client.get("/api/v1/remote-players").json() == []


def test_status_play_command_and_error_codes(alembic_client, vlc):
    player = _create(alembic_client).json()
    status = alembic_client.get(f"/api/v1/remote-players/{player['id']}/status").json()
    assert status == {"state": "playing", "title": "Arena", "position_s": 5, "length_s": None, "volume_pct": 50, "message": None}
    play = alembic_client.post(f"/api/v1/remote-players/{player['id']}/play", json={"content_id": IH, "title": "Arena"})
    assert play.status_code == 202 and play.json()["url"].endswith(f"/tuner/stream/{IH}.ts")
    assert alembic_client.post(f"/api/v1/remote-players/{player['id']}/command", json={"command": "volume", "value": 50}).status_code == 204
    assert alembic_client.post(f"/api/v1/remote-players/{player['id']}/command", json={"command": "seek", "value": 1}).status_code == 422

    vlc["handler"] = lambda r: httpx.Response(401)
    response = alembic_client.get(f"/api/v1/remote-players/{player['id']}/status")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "REMOTE_PLAYER_AUTH" and response.json()["error"]["context"]["kind"] == "wrong_password"

    def down(request):
        raise httpx.ConnectError("down")
    vlc["handler"] = down
    assert alembic_client.get(f"/api/v1/remote-players/{player['id']}/status").json()["error"]["code"] == "REMOTE_PLAYER_UNREACHABLE"

    vlc["handler"] = lambda r: httpx.Response(200, text="<pre>bad argument</pre>", headers={"Content-Type": "text/html"})
    response = alembic_client.post(f"/api/v1/remote-players/{player['id']}/command", json={"command": "stop"})
    assert response.status_code == 400 and response.json()["error"]["code"] == "REMOTE_PLAYER_COMMAND_FAILED"


def test_scan_validation_and_default(alembic_client, vlc):
    assert alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "8.8.8.0/22"}).json()["error"]["code"] == "SCAN_CIDR_NOT_PRIVATE"
    assert alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "10.0.0.0/8"}).json()["error"]["code"] == "SCAN_TOO_LARGE"
    body = alembic_client.get("/api/v1/remote-players/scan/default").json()
    assert body["cidr"] is None and body["hint"]
    response = alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "127.0.0.1/32", "ports": [1], "timeout_ms": 100})
    assert response.json()["error"]["code"] == "SCAN_CIDR_NOT_PRIVATE"
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_remote_players_api.py`
Expected: FAIL (404s).

- [ ] **Step 3: Schemas**

Create `backend/app/schemas/remote_players.py`:

```python
"""DTOs for /api/v1/remote-players (spec 6.1)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PlayerKind = Literal["vlc", "kodi"]
PlayerCommand = Literal["pause", "resume", "stop", "volume"]


class RemotePlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    kind: PlayerKind
    host: str = Field(..., min_length=1, max_length=255, description="Hostname or IP, no scheme")
    port: int = Field(8080, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=255, description="Kodi only; default kodi")
    base_url_id: Optional[int] = Field(None, description="Stream link format; null = server relay URL")


class RemotePlayerCreate(RemotePlayerBase):
    password: Optional[str] = Field(None, max_length=1024)


class RemotePlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    kind: Optional[PlayerKind] = None
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=1024, description="omit = keep, empty string = clear")
    base_url_id: Optional[int] = None
    clear_base_url: bool = False


class RemotePlayerResponse(RemotePlayerBase):
    id: int
    has_password: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RemotePlayerTestRequest(BaseModel):
    kind: PlayerKind
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(8080, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    id: Optional[int] = Field(None, description="Use this saved player's password when none is given")


class TunerAccessResponse(BaseModel):
    addresses: List[str]
    allowed: bool


class RemotePlayerProbeResponse(BaseModel):
    reachable: bool
    authenticated: bool
    version: Optional[str] = None
    message: str
    hint: Optional[str] = None
    tuner_access: TunerAccessResponse


class RemotePlayerStatusResponse(BaseModel):
    state: Literal["playing", "paused", "stopped"]
    title: Optional[str] = None
    position_s: Optional[int] = None
    length_s: Optional[int] = None
    volume_pct: Optional[int] = None
    message: Optional[str] = None


class RemotePlayerPlayRequest(BaseModel):
    content_id: str = Field(..., pattern=r"^[0-9a-fA-F]{40}$")
    title: Optional[str] = None


class RemotePlayerPlayResponse(BaseModel):
    url: str


class RemotePlayerCommandRequest(BaseModel):
    command: PlayerCommand
    value: Optional[int] = Field(None, ge=0, le=200)


class ScanRequest(BaseModel):
    cidr: str
    ports: List[int] = Field(default_factory=lambda: [8080])
    timeout_ms: int = Field(400, ge=50, le=5000)


class ScanHitResponse(BaseModel):
    host: str
    port: int
    kind: Literal["vlc", "kodi", "unknown"]
    hint: str


class ScanResultResponse(BaseModel):
    hosts: List[ScanHitResponse]
    scanned: int
    duration_ms: int


class ScanDefaultResponse(BaseModel):
    cidr: Optional[str] = None
    hint: str
```

- [ ] **Step 4: Endpoints**

Create `backend/app/api/endpoints/remote_players.py`:

```python
"""VLC/Kodi remote players (spec 6.1). Sync handlers: the drivers block for up to a few seconds."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.models.models import RemotePlayer
from app.repositories.settings_repository import SettingsRepository
from app.schemas.remote_players import (
    RemotePlayerCommandRequest, RemotePlayerCreate, RemotePlayerPlayRequest, RemotePlayerPlayResponse,
    RemotePlayerProbeResponse, RemotePlayerResponse, RemotePlayerStatusResponse, RemotePlayerTestRequest,
    RemotePlayerUpdate, ScanDefaultResponse, ScanRequest, ScanResultResponse, TunerAccessResponse,
)
from app.services.public_url_service import resolve_public_base_url
from app.services.remote_players.base import PlayerAuthError, PlayerCommandError, PlayerUnreachable, new_client
from app.services.remote_players.scan import ScanValidationError, default_scan_cidr, scan_network, validate_scan_request
from app.services.remote_players.service import RemotePlayerService
from app.utils.url_guard import BlockedURLError

router = APIRouter(tags=["remote-players"])

_client_factory = new_client  # tests swap in a MockTransport factory


def _service(db: Session = Depends(get_db)) -> RemotePlayerService:
    return RemotePlayerService(db, client_factory=_client_factory)


def _response(player: RemotePlayer) -> RemotePlayerResponse:
    return RemotePlayerResponse(
        id=player.id, name=player.name, kind=player.kind, host=player.host, port=player.port, username=player.username,
        base_url_id=player.base_url_id, has_password=bool(player.password), created_at=player.created_at, updated_at=player.updated_at,
    )


def _player_or_404(service: RemotePlayerService, player_id: int) -> RemotePlayer:
    player = service.repo.get(player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remote player not found")
    return player


def _validated_host(service: RemotePlayerService, host: str) -> str:
    try:
        return service.validate_host(host)
    except (BlockedURLError, ValueError) as exc:
        raise APIError(code="REMOTE_PLAYER_HOST_FORBIDDEN", message=str(exc), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                       context={"host": host}) from exc


def _translate(exc: Exception) -> APIError:
    if isinstance(exc, PlayerAuthError):
        return APIError(code="REMOTE_PLAYER_AUTH", message=str(exc), status_code=status.HTTP_502_BAD_GATEWAY, context={"kind": exc.kind})
    if isinstance(exc, PlayerUnreachable):
        return APIError(code="REMOTE_PLAYER_UNREACHABLE", message=str(exc), status_code=status.HTTP_502_BAD_GATEWAY)
    if isinstance(exc, PlayerCommandError):
        return APIError(code="REMOTE_PLAYER_COMMAND_FAILED", message=str(exc), status_code=status.HTTP_400_BAD_REQUEST)
    raise exc


@router.get("", response_model=List[RemotePlayerResponse])
def list_players(service: RemotePlayerService = Depends(_service)):
    return [_response(p) for p in service.repo.get_all()]


@router.post("", response_model=RemotePlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(payload: RemotePlayerCreate, service: RemotePlayerService = Depends(_service)):
    host = _validated_host(service, payload.host)
    if service.repo.get_by_name(payload.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Remote player '{payload.name}' already exists")
    player = service.repo.create(name=payload.name, kind=payload.kind, host=host, port=payload.port, username=payload.username,
                                 password=payload.password, base_url_id=payload.base_url_id)
    return _response(player)


@router.patch("/{player_id}", response_model=RemotePlayerResponse)
def update_player(player_id: int, payload: RemotePlayerUpdate, service: RemotePlayerService = Depends(_service)):
    player = _player_or_404(service, player_id)
    if payload.name and payload.name != player.name and service.repo.get_by_name(payload.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Remote player '{payload.name}' already exists")
    host = _validated_host(service, payload.host) if payload.host else None
    player = service.repo.update(player, name=payload.name, kind=payload.kind, host=host, port=payload.port, username=payload.username,
                                 password=payload.password, base_url_id=payload.base_url_id)
    if payload.clear_base_url:
        player = service.repo.clear_base_url(player)
    return _response(player)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, service: RemotePlayerService = Depends(_service)):
    service.repo.delete(_player_or_404(service, player_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _probe(service: RemotePlayerService, kind: str, host: str, port: int, username, password, stored_id) -> RemotePlayerProbeResponse:
    try:
        probe, access = service.probe(kind, host, port, username, password, stored_id=stored_id)
    except PlayerUnreachable as exc:
        return RemotePlayerProbeResponse(reachable=False, authenticated=False, version=None, message=str(exc),
                                         hint="Check the address and port, and that the player is running with its web interface enabled.",
                                         tuner_access=TunerAccessResponse(addresses=[], allowed=True))
    return RemotePlayerProbeResponse(reachable=probe.reachable, authenticated=probe.authenticated, version=probe.version,
                                     message=probe.message, hint=probe.hint,
                                     tuner_access=TunerAccessResponse(addresses=access.addresses, allowed=access.allowed))


@router.post("/test", response_model=RemotePlayerProbeResponse, summary="Probe a player before saving it")
def test_player(payload: RemotePlayerTestRequest, service: RemotePlayerService = Depends(_service)):
    host = _validated_host(service, payload.host)
    return _probe(service, payload.kind, host, payload.port, payload.username, payload.password, payload.id)


@router.post("/{player_id}/test", response_model=RemotePlayerProbeResponse)
def test_saved_player(player_id: int, service: RemotePlayerService = Depends(_service)):
    player = _player_or_404(service, player_id)
    return _probe(service, player.kind, player.host, player.port, player.username, player.password, None)


@router.get("/{player_id}/status", response_model=RemotePlayerStatusResponse)
def player_status(player_id: int, service: RemotePlayerService = Depends(_service)):
    player = _player_or_404(service, player_id)
    try:
        status_ = service.status(player)
    except (PlayerAuthError, PlayerUnreachable, PlayerCommandError) as exc:
        raise _translate(exc) from exc
    return RemotePlayerStatusResponse(**status_.__dict__)


@router.post("/{player_id}/play", response_model=RemotePlayerPlayResponse, status_code=status.HTTP_202_ACCEPTED)
def play_on_player(player_id: int, payload: RemotePlayerPlayRequest, request: Request, service: RemotePlayerService = Depends(_service)):
    player = _player_or_404(service, player_id)
    public = resolve_public_base_url(request, SettingsRepository(service.db)).url
    try:
        url = service.play(player, payload.content_id.lower(), public, payload.title or payload.content_id)
    except (PlayerAuthError, PlayerUnreachable, PlayerCommandError) as exc:
        raise _translate(exc) from exc
    return RemotePlayerPlayResponse(url=url)


@router.post("/{player_id}/command", status_code=status.HTTP_204_NO_CONTENT)
def player_command(player_id: int, payload: RemotePlayerCommandRequest, service: RemotePlayerService = Depends(_service)):
    player = _player_or_404(service, player_id)
    try:
        service.command(player, payload.command, payload.value)
    except (PlayerAuthError, PlayerUnreachable, PlayerCommandError) as exc:
        raise _translate(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/scan", response_model=ScanResultResponse, summary="Find VLC/Kodi web interfaces on a private network")
async def scan(payload: ScanRequest):
    try:
        network, ports = validate_scan_request(payload.cidr, payload.ports)
    except ScanValidationError as exc:
        raise APIError(code=exc.code, message=str(exc), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY) from exc
    outcome = await scan_network(network, ports, timeout_ms=payload.timeout_ms, client_factory=_client_factory)
    return ScanResultResponse(hosts=[h.__dict__ for h in outcome.hits], scanned=outcome.scanned, duration_ms=outcome.duration_ms)


@router.get("/scan/default", response_model=ScanDefaultResponse)
def scan_default(request: Request):
    cidr = default_scan_cidr(request.client.host if request.client else None)
    hint = "Your network, guessed from your address." if cidr else "Type your network, for example 192.168.1.0/24 (this server cannot see it from here)."
    return ScanDefaultResponse(cidr=cidr, hint=hint)
```

`backend/app/api/api.py`: `api_router.include_router(remote_players.router, prefix="/remote-players", tags=["remote-players"])` (add the import).

Note the route order: `/test`, `/scan`, `/scan/default` are declared before `/{player_id}` routes with the same method where ambiguity exists (`POST /test` vs `POST /{player_id}/test` are distinct paths, `GET /scan/default` vs `GET /{player_id}/status` are distinct). Keep `POST /scan` above any `POST /{player_id}` route — there is none, but keep the ordering anyway.

- [ ] **Step 5: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_remote_players_api.py backend/tests/test_error_contracts.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/remote_players.py backend/app/api/endpoints/remote_players.py backend/app/api/api.py backend/tests/test_remote_players_api.py
git commit -m "feat(api): remote players CRUD, probe, status, play, command and scan"
```

---

### Task 5: Frontend service and hooks for remote players

**Files:**
- Create: `frontend/src/services/remotePlayerService.ts`, `frontend/src/hooks/useRemotePlayers.ts`
- Test: `frontend/src/__tests__/remotePlayerService.test.ts`

**Interfaces:**
- Produces types `RemotePlayer`, `RemotePlayerKind`, `RemotePlayerCreate`, `RemotePlayerUpdate`, `RemotePlayerProbe`, `RemotePlayerStatus`, `ScanHit`, `ScanResult`; `remotePlayerService.{list, create, update, remove, test, testSaved, status, play, command, scan, scanDefault}`; hooks `useRemotePlayers()`, `useCreateRemotePlayer()`, `useUpdateRemotePlayer()`, `useDeleteRemotePlayer()`, `useTestRemotePlayer()`, `useRemotePlayerStatus(id, enabled)` (5 s poll, `retry: false`), `usePlayOnRemotePlayer()`, `useRemotePlayerCommand()`, `useScanRemotePlayers()`, `useScanDefault()`. Query key `REMOTE_PLAYERS_QUERY_KEY = ['remote-players']`.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/__tests__/remotePlayerService.test.ts`:

```ts
import apiClient from '../services/apiClient';
import { remotePlayerService } from '../services/remotePlayerService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), patch: jest.fn(), delete: jest.fn() },
}));

describe('remotePlayerService', () => {
  beforeEach(() => jest.clearAllMocks());

  it('uses /v1/remote-players paths', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { id: 1 } });
    (apiClient.patch as jest.Mock).mockResolvedValue({ data: { id: 1 } });
    (apiClient.delete as jest.Mock).mockResolvedValue({});
    await remotePlayerService.list();
    await remotePlayerService.create({ name: 'a', kind: 'vlc', host: 'h', port: 8080 });
    await remotePlayerService.update(1, { name: 'b' });
    await remotePlayerService.remove(1);
    await remotePlayerService.test({ kind: 'vlc', host: 'h', port: 8080 });
    await remotePlayerService.status(1);
    await remotePlayerService.play(1, 'a'.repeat(40), 'Arena');
    await remotePlayerService.command(1, 'volume', 50);
    await remotePlayerService.scan({ cidr: '192.168.1.0/24' });
    await remotePlayerService.scanDefault();
    expect(apiClient.get).toHaveBeenCalledWith('/v1/remote-players');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players', { name: 'a', kind: 'vlc', host: 'h', port: 8080 });
    expect(apiClient.patch).toHaveBeenCalledWith('/v1/remote-players/1', { name: 'b' });
    expect(apiClient.delete).toHaveBeenCalledWith('/v1/remote-players/1');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/test', { kind: 'vlc', host: 'h', port: 8080 });
    expect(apiClient.get).toHaveBeenCalledWith('/v1/remote-players/1/status');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/1/play', { content_id: 'a'.repeat(40), title: 'Arena' });
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/1/command', { command: 'volume', value: 50 });
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/scan', { cidr: '192.168.1.0/24' });
    expect(apiClient.get).toHaveBeenCalledWith('/v1/remote-players/scan/default');
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npm test -- remotePlayerService.test.ts`
Expected: FAIL.

- [ ] **Step 3: Implement**

`frontend/src/services/remotePlayerService.ts`:

```ts
import apiClient from './apiClient';

export type RemotePlayerKind = 'vlc' | 'kodi';
export type RemotePlayerCommand = 'pause' | 'resume' | 'stop' | 'volume';

export interface RemotePlayer {
  id: number;
  name: string;
  kind: RemotePlayerKind;
  host: string;
  port: number;
  username: string | null;
  base_url_id: number | null;
  has_password: boolean;
  created_at: string;
  updated_at: string;
}

export interface RemotePlayerCreate {
  name: string;
  kind: RemotePlayerKind;
  host: string;
  port: number;
  username?: string | null;
  password?: string | null;
  base_url_id?: number | null;
}

export interface RemotePlayerUpdate extends Partial<RemotePlayerCreate> {
  clear_base_url?: boolean;
}

export interface RemotePlayerTestRequest {
  kind: RemotePlayerKind;
  host: string;
  port: number;
  username?: string | null;
  password?: string | null;
  id?: number;
}

export interface TunerAccess {
  addresses: string[];
  allowed: boolean;
}

export interface RemotePlayerProbe {
  reachable: boolean;
  authenticated: boolean;
  version: string | null;
  message: string;
  hint: string | null;
  tuner_access: TunerAccess;
}

export interface RemotePlayerStatus {
  state: 'playing' | 'paused' | 'stopped';
  title: string | null;
  position_s: number | null;
  length_s: number | null;
  volume_pct: number | null;
  message: string | null;
}

export interface ScanHit {
  host: string;
  port: number;
  kind: RemotePlayerKind | 'unknown';
  hint: string;
}

export interface ScanResult {
  hosts: ScanHit[];
  scanned: number;
  duration_ms: number;
}

export interface ScanRequest {
  cidr: string;
  ports?: number[];
  timeout_ms?: number;
}

export interface ScanDefault {
  cidr: string | null;
  hint: string;
}

const BASE_URL = '/v1/remote-players';

export const remotePlayerService = {
  list: async (): Promise<RemotePlayer[]> => (await apiClient.get<RemotePlayer[]>(BASE_URL)).data,
  create: async (body: RemotePlayerCreate): Promise<RemotePlayer> => (await apiClient.post<RemotePlayer>(BASE_URL, body)).data,
  update: async (id: number, body: RemotePlayerUpdate): Promise<RemotePlayer> => (await apiClient.patch<RemotePlayer>(`${BASE_URL}/${id}`, body)).data,
  remove: async (id: number): Promise<void> => { await apiClient.delete(`${BASE_URL}/${id}`); },
  test: async (body: RemotePlayerTestRequest): Promise<RemotePlayerProbe> => (await apiClient.post<RemotePlayerProbe>(`${BASE_URL}/test`, body)).data,
  testSaved: async (id: number): Promise<RemotePlayerProbe> => (await apiClient.post<RemotePlayerProbe>(`${BASE_URL}/${id}/test`)).data,
  status: async (id: number): Promise<RemotePlayerStatus> => (await apiClient.get<RemotePlayerStatus>(`${BASE_URL}/${id}/status`)).data,
  play: async (id: number, contentId: string, title?: string): Promise<{ url: string }> =>
    (await apiClient.post<{ url: string }>(`${BASE_URL}/${id}/play`, { content_id: contentId, title })).data,
  command: async (id: number, command: RemotePlayerCommand, value?: number): Promise<void> => {
    await apiClient.post(`${BASE_URL}/${id}/command`, value === undefined ? { command } : { command, value });
  },
  scan: async (body: ScanRequest): Promise<ScanResult> => (await apiClient.post<ScanResult>(`${BASE_URL}/scan`, body)).data,
  scanDefault: async (): Promise<ScanDefault> => (await apiClient.get<ScanDefault>(`${BASE_URL}/scan/default`)).data,
};
```

`frontend/src/hooks/useRemotePlayers.ts`:

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../services/apiErrors';
import {
  remotePlayerService,
  type RemotePlayer,
  type RemotePlayerCommand,
  type RemotePlayerCreate,
  type RemotePlayerProbe,
  type RemotePlayerStatus,
  type RemotePlayerTestRequest,
  type RemotePlayerUpdate,
  type ScanRequest,
  type ScanResult,
} from '../services/remotePlayerService';

export const REMOTE_PLAYERS_QUERY_KEY = ['remote-players'] as const;
export const remotePlayerStatusKey = (id: number) => ['remote-players', id, 'status'] as const;

export const useRemotePlayers = () =>
  useQuery<RemotePlayer[], ApiError>({ queryKey: REMOTE_PLAYERS_QUERY_KEY, queryFn: remotePlayerService.list });

const useInvalidatePlayers = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: REMOTE_PLAYERS_QUERY_KEY });
};

export const useCreateRemotePlayer = () => {
  const invalidate = useInvalidatePlayers();
  return useMutation<RemotePlayer, ApiError, RemotePlayerCreate>({ mutationFn: remotePlayerService.create, onSuccess: () => void invalidate() });
};

export const useUpdateRemotePlayer = () => {
  const invalidate = useInvalidatePlayers();
  return useMutation<RemotePlayer, ApiError, { id: number; data: RemotePlayerUpdate }>({
    mutationFn: ({ id, data }) => remotePlayerService.update(id, data),
    onSuccess: () => void invalidate(),
  });
};

export const useDeleteRemotePlayer = () => {
  const invalidate = useInvalidatePlayers();
  return useMutation<void, ApiError, number>({ mutationFn: remotePlayerService.remove, onSuccess: () => void invalidate() });
};

export const useTestRemotePlayer = () =>
  useMutation<RemotePlayerProbe, ApiError, RemotePlayerTestRequest>({ mutationFn: remotePlayerService.test });

/** Live status for one player card; polled while the card is on screen. */
export const useRemotePlayerStatus = (id: number, enabled = true) =>
  useQuery<RemotePlayerStatus, ApiError>({
    queryKey: remotePlayerStatusKey(id),
    queryFn: () => remotePlayerService.status(id),
    enabled,
    retry: false,
    refetchInterval: 5_000,
  });

export const usePlayOnRemotePlayer = () =>
  useMutation<{ url: string }, ApiError, { id: number; contentId: string; title?: string }>({
    mutationFn: ({ id, contentId, title }) => remotePlayerService.play(id, contentId, title),
  });

export const useRemotePlayerCommand = () => {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, { id: number; command: RemotePlayerCommand; value?: number }>({
    mutationFn: ({ id, command, value }) => remotePlayerService.command(id, command, value),
    onSuccess: (_data, { id }) => void queryClient.invalidateQueries({ queryKey: remotePlayerStatusKey(id) }),
  });
};

export const useScanRemotePlayers = () => useMutation<ScanResult, ApiError, ScanRequest>({ mutationFn: remotePlayerService.scan });

export const useScanDefault = (enabled: boolean) =>
  useQuery({ queryKey: ['remote-players', 'scan-default'], queryFn: remotePlayerService.scanDefault, enabled, staleTime: 60_000 });
```

- [ ] **Step 4: Run**

Run: `cd frontend && npm test -- remotePlayerService.test.ts && npm run lint -- --max-warnings=0 && npm run typecheck`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/remotePlayerService.ts frontend/src/hooks/useRemotePlayers.ts frontend/src/__tests__/remotePlayerService.test.ts
git commit -m "feat(frontend): remote player service and hooks"
```

---

### Task 6: Integrations page, remote player UI, "Play on…" everywhere

**Files:**
- Create: `frontend/src/pages/Integrations.tsx`, `frontend/src/components/integrations/PublicAddressSection.tsx`, `frontend/src/components/integrations/WebPlayerSection.tsx`, `frontend/src/components/integrations/RemotePlayersSection.tsx`, `frontend/src/components/integrations/RemotePlayerDialog.tsx`, `frontend/src/components/integrations/FindPlayersDialog.tsx`, `frontend/src/components/player/PlayOnMenu.tsx`, `frontend/src/components/player/ChannelPickerDialog.tsx`
- Modify: `frontend/src/components/layout/navItems.tsx`, `frontend/src/App.tsx`, `frontend/src/components/channels/ChannelRowActions.tsx` (+ `onPlayOn`), `frontend/src/pages/AcestreamChannels.tsx` (PlayOnMenu in the dialog and the row menu), `frontend/src/__tests__/routes.test.tsx`, `e2e/src/pages/app-shell.ts` (NavLabel/NAV_ROUTES)
- Tests: `frontend/src/__tests__/Integrations.test.tsx`, `frontend/src/__tests__/PlayOnMenu.test.tsx`, `frontend/src/__tests__/ChannelPickerDialog.test.tsx`, plus `ChannelRowActions.test.tsx`/`ChannelTable.test.tsx`/`ChannelCardList.test.tsx`/`AcestreamChannelsPage.test.tsx` updates for `onPlayOn`

**Interfaces:**
- Produces: route `/integrations` (nav "Integrations", System section, `HubRounded` icon, above Settings); `PlayOnMenu` props `{ contentId: string; title: string; variant?: 'button' | 'menu-items'; onDone?: () => void }` (button variant = a "Play on…" button with a menu; used by the player dialog); `ChannelActionHandlers.onPlayOn(channel)` opens the same menu from the row; `ChannelPickerDialog` props `{ open: boolean; player: RemotePlayer | null; onClose: () => void }`; `RemotePlayersSection` (self-contained, owns its dialogs and snackbar), `PublicAddressSection`, `WebPlayerSection`.

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/__tests__/PlayOnMenu.test.tsx`:

```tsx
import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PlayOnMenu from '../components/player/PlayOnMenu';
import { createAppTheme } from '../theme';

const mockPlayers = jest.fn();
const mockPlay = jest.fn();
jest.mock('../hooks/useRemotePlayers', () => ({
  useRemotePlayers: () => mockPlayers(),
  usePlayOnRemotePlayer: () => ({ mutateAsync: mockPlay, isPending: false }),
}));

const mount = () => render(
  <ThemeProvider theme={createAppTheme('light')}>
    <PlayOnMenu contentId={'a'.repeat(40)} title="Arena TV" />
  </ThemeProvider>
);

it('lists players and sends the channel', async () => {
  mockPlayers.mockReturnValue({ data: [{ id: 1, name: 'Living room', kind: 'vlc' }, { id: 2, name: 'Kitchen', kind: 'kodi' }], isLoading: false });
  mockPlay.mockResolvedValue({ url: 'http://x' });
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
  fireEvent.click(screen.getByRole('menuitem', { name: 'Living room (VLC)' }));
  await waitFor(() => expect(mockPlay).toHaveBeenCalledWith({ id: 1, contentId: 'a'.repeat(40), title: 'Arena TV' }));
  expect(await screen.findByText('Sent Arena TV to Living room.')).toBeInTheDocument();
});

it('points at the Integrations page when there are no players', () => {
  mockPlayers.mockReturnValue({ data: [], isLoading: false });
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
  expect(screen.getByRole('menuitem', { name: /Add a player/ })).toHaveAttribute('href', '/integrations');
});

it('explains a wrong password without the API-token notice', async () => {
  mockPlayers.mockReturnValue({ data: [{ id: 1, name: 'Living room', kind: 'vlc' }], isLoading: false });
  const { ApiError } = jest.requireActual('../services/apiErrors');
  mockPlay.mockRejectedValue(new ApiError('nope', 502, 'server', { code: 'REMOTE_PLAYER_AUTH', context: { kind: 'wrong_password' } }));
  const listener = jest.fn();
  window.addEventListener('acestream:api-token-required', listener);
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
  fireEvent.click(screen.getByRole('menuitem', { name: 'Living room (VLC)' }));
  expect(await screen.findByText(/Check the password/)).toBeInTheDocument();
  expect(listener).not.toHaveBeenCalled();
});
```

(Adapt the `ApiError` constructor call to its real signature in `services/apiErrors.ts`; the assertion that matters is `code === 'REMOTE_PLAYER_AUTH'` → guided copy.)

Create `frontend/src/__tests__/ChannelPickerDialog.test.tsx`:

```tsx
import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ChannelPickerDialog from '../components/player/ChannelPickerDialog';
import { createAppTheme } from '../theme';

const mockCatalog = jest.fn();
const mockChannels = jest.fn();
const mockPlay = jest.fn();
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: (...args: unknown[]) => mockCatalog(...args) }));
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannels: (...args: unknown[]) => mockChannels(...args) }));
jest.mock('../hooks/useRemotePlayers', () => ({ usePlayOnRemotePlayer: () => ({ mutateAsync: mockPlay, isPending: false }) }));

const player = { id: 1, name: 'Living room', kind: 'vlc' as const, host: 'h', port: 8080, username: null, base_url_id: null, has_password: true, created_at: '', updated_at: '' };

it('picks a TV channel and sends its best stream', async () => {
  mockCatalog.mockReturnValue({ data: [
    { id: 7, name: 'Arena TV', is_active: true, acestream_channels: [{ id: 'best', name: 'Feed 1', is_online: true }, { id: 'other', name: 'Feed 2' }] },
    { id: 8, name: 'Empty', is_active: true, acestream_channels: [] },
  ], isLoading: false });
  mockChannels.mockReturnValue({ data: { items: [] }, isLoading: false });
  mockPlay.mockResolvedValue({ url: 'x' });
  const onClose = jest.fn();
  render(<ThemeProvider theme={createAppTheme('light')}><ChannelPickerDialog open player={player} onClose={onClose} /></ThemeProvider>);
  const input = screen.getByRole('combobox', { name: 'Channel' });
  fireEvent.mouseDown(input);
  expect(screen.queryByText('Empty')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('option', { name: /Arena TV/ }));
  fireEvent.click(screen.getByRole('button', { name: 'Send to Living room' }));
  await waitFor(() => expect(mockPlay).toHaveBeenCalledWith({ id: 1, contentId: 'best', title: 'Arena TV' }));
  expect(onClose).toHaveBeenCalled();
});

it('switches to raw streams', () => {
  mockCatalog.mockReturnValue({ data: [], isLoading: false });
  mockChannels.mockReturnValue({ data: { items: [{ id: 's1', name: 'Raw feed', group: 'Sports', is_online: true }] }, isLoading: false });
  render(<ThemeProvider theme={createAppTheme('light')}><ChannelPickerDialog open player={player} onClose={jest.fn()} /></ThemeProvider>);
  fireEvent.click(screen.getByRole('button', { name: 'Streams' }));
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Channel' }));
  expect(screen.getByRole('option', { name: /Raw feed/ })).toBeInTheDocument();
});
```

Create `frontend/src/__tests__/Integrations.test.tsx`:

```tsx
import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import Integrations from '../pages/Integrations';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockPublicUrl = jest.fn();
const mockUpdatePublicBaseUrl = jest.fn();
const mockCapabilities = jest.fn();
const mockSessions = jest.fn();
const mockPlayers = jest.fn();
const mockStatus = jest.fn();
const mockDelete = jest.fn();
const mockCommand = jest.fn();
const mockTest = jest.fn();

jest.mock('../hooks/useSystemServices', () => ({ usePublicUrl: () => mockPublicUrl(), PUBLIC_URL_QUERY_KEY: ['system', 'public-url'] }));
jest.mock('../services/configService', () => ({ configService: { updatePublicBaseUrl: (...a: unknown[]) => mockUpdatePublicBaseUrl(...a) } }));
jest.mock('../hooks/usePlayer', () => ({ usePlayerCapabilities: () => mockCapabilities(), usePlayerSessions: () => mockSessions() }));
jest.mock('../hooks/useRemotePlayers', () => ({
  useRemotePlayers: () => mockPlayers(),
  useRemotePlayerStatus: (id: number) => mockStatus(id),
  useDeleteRemotePlayer: () => ({ mutateAsync: mockDelete, isPending: false }),
  useRemotePlayerCommand: () => ({ mutateAsync: mockCommand, isPending: false }),
  useCreateRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useTestRemotePlayer: () => ({ mutateAsync: mockTest, isPending: false }),
  useScanRemotePlayers: () => ({ mutateAsync: jest.fn(), isPending: false, data: undefined }),
  useScanDefault: () => ({ data: { cidr: '192.168.1.0/24', hint: '' } }),
  usePlayOnRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));
jest.mock('../hooks/useBaseUrls', () => ({ useBaseUrls: () => ({ data: [], isLoading: false }) }));
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: () => ({ data: [], isLoading: false }) }));
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannels: () => ({ data: { items: [] }, isLoading: false }) }));
jest.mock('@tanstack/react-query', () => ({ ...jest.requireActual('@tanstack/react-query'), useQueryClient: () => ({ invalidateQueries: jest.fn() }) }));

const renderPage = () => render(
  <ThemeProvider theme={createAppTheme('light')}>
    <TestMemoryRouter><Integrations /></TestMemoryRouter>
  </ThemeProvider>
);

describe('Integrations page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPublicUrl.mockReturnValue({ data: { url: 'http://localhost:8000', source: 'request', warnings: ['localhost', 'unset'] }, isLoading: false });
    mockCapabilities.mockReturnValue({ data: { ffmpeg_available: true, ffmpeg_path: '/opt/ffmpeg/bin/ffmpeg', max_sessions: 3, hls_dir: '/tmp/x' } });
    mockSessions.mockReturnValue({ data: { sessions: [] } });
    mockPlayers.mockReturnValue({ data: [{ id: 1, name: 'Living room', kind: 'vlc', host: '192.168.1.20', port: 8080, username: null, base_url_id: null, has_password: true, created_at: '', updated_at: '' }], isLoading: false });
    mockStatus.mockReturnValue({ data: { state: 'playing', title: 'Arena TV', position_s: 61, length_s: null, volume_pct: 50, message: null }, error: null });
  });

  it('renders the page skeleton with the three sections', () => {
    renderPage();
    expect(screen.getByRole('heading', { level: 1, name: 'Integrations' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)).toEqual(['Public address', 'Web player', 'Remote players']);
    expect(screen.getByRole('status', { name: 'Integration summary' })).toHaveTextContent('Players 1');
  });

  it('warns about a localhost public address and saves a new one', async () => {
    mockUpdatePublicBaseUrl.mockResolvedValue(undefined);
    renderPage();
    const section = screen.getByRole('region', { name: 'Public address' });
    expect(within(section).getByRole('alert')).toHaveTextContent(/localhost/);
    fireEvent.change(within(section).getByRole('textbox', { name: 'Public address' }), { target: { value: 'http://192.168.1.10:8000' } });
    fireEvent.click(within(section).getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(mockUpdatePublicBaseUrl).toHaveBeenCalledWith('http://192.168.1.10:8000'));
  });

  it('shows player cards with live status, transport and a menu with confirm on delete', async () => {
    mockDelete.mockResolvedValue(undefined);
    renderPage();
    const card = screen.getByRole('group', { name: 'Player Living room' });
    expect(within(card).getByText(/Playing.*Arena TV/)).toBeInTheDocument();
    fireEvent.click(within(card).getByRole('button', { name: 'Pause Living room' }));
    await waitFor(() => expect(mockCommand).toHaveBeenCalledWith({ id: 1, command: 'pause' }));
    fireEvent.click(within(card).getByRole('button', { name: 'More actions for Living room' }));
    expect(screen.getByRole('menuitem', { name: 'Send channel…' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete Living room?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(mockDelete).toHaveBeenCalledWith(1));
  });

  it('opens the add dialog and runs Test connection with the guided VLC message', async () => {
    mockTest.mockResolvedValue({ reachable: true, authenticated: false, version: null, message: 'no password', hint: "VLC's web interface has no password. In VLC: Tools > Preferences", tuner_access: { addresses: ['192.168.1.20'], allowed: true } });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Add player' }));
    const dialog = await screen.findByRole('dialog', { name: 'Add player' });
    fireEvent.change(within(dialog).getByRole('textbox', { name: 'Name' }), { target: { value: 'Bedroom' } });
    fireEvent.change(within(dialog).getByRole('textbox', { name: 'Host' }), { target: { value: '192.168.1.21' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }));
    expect(await within(dialog).findByText(/Tools > Preferences/)).toBeInTheDocument();
    expect(mockTest).toHaveBeenCalledWith(expect.objectContaining({ kind: 'vlc', host: '192.168.1.21', port: 8080 }));
  });
});
```

Update `routes.test.tsx` label list to include `'Integrations'` before `'Settings'` and add `expect(getNavTitle('/integrations')).toBe('Integrations');`. Update `ChannelRowActions.test.tsx` / `ChannelTable.test.tsx` / `ChannelCardList.test.tsx` / `AcestreamChannelsPage.test.tsx` handler fixtures with `onPlayOn: jest.fn()` and one assertion in `ChannelRowActions.test.tsx` that the row menu has a `Play on…` item calling `onPlayOn`.

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npm test -- PlayOnMenu.test.tsx ChannelPickerDialog.test.tsx Integrations.test.tsx routes.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement the shared player pieces**

`frontend/src/hooks/usePlayer.ts` — add:

```ts
export const PLAYER_SESSIONS_QUERY_KEY = ['player', 'sessions'] as const;
export const usePlayerSessions = () =>
  useQuery({ queryKey: PLAYER_SESSIONS_QUERY_KEY, queryFn: playerService.listSessions, refetchInterval: 10_000 });
```
and in `playerService.ts`: `listSessions: async (): Promise<{ sessions: PlayerSessionStatus[] }> => (await apiClient.get(`${BASE_URL}/sessions`)).data,`.

`frontend/src/components/player/playerCopy.ts` — add:

```ts
import type { ApiError } from '../../services/apiErrors';

/** Guided copy for remote-player failures; never the API-token notice (that is a 401, these are 502/400). */
export const describeRemotePlayerError = (error: ApiError): string => {
  if (error.code === 'REMOTE_PLAYER_AUTH') {
    const kind = (error.context as { kind?: string } | undefined)?.kind;
    return kind === 'no_password'
      ? "VLC's web interface has no password. In VLC: Tools > Preferences > All > Interface > Main interfaces > Web, then Lua > Lua HTTP > Password."
      : 'Check the password (VLC: Lua HTTP password; Kodi: Settings > Services > Control).';
  }
  if (error.code === 'REMOTE_PLAYER_UNREACHABLE') return 'The player did not answer. Is it running with its web interface on?';
  if (error.code === 'REMOTE_PLAYER_COMMAND_FAILED') return `The player refused the command: ${error.message}`;
  return error.message || 'Something went wrong talking to the player.';
};
```

`frontend/src/components/player/PlayOnMenu.tsx`:

```tsx
import React, { useState } from 'react';
import { Alert, Button, ListItemIcon, ListItemText, Menu, MenuItem, Snackbar } from '@mui/material';
import CastRoundedIcon from '@mui/icons-material/CastRounded';
import { Link as RouterLink } from 'react-router-dom';
import { usePlayOnRemotePlayer, useRemotePlayers } from '../../hooks/useRemotePlayers';
import { ApiError } from '../../services/apiErrors';
import { describeRemotePlayerError } from './playerCopy';

export interface PlayOnMenuProps {
  contentId: string;
  title: string;
  /** Rendered as a button that opens the menu (default) or as bare menu items for an existing menu. */
  variant?: 'button';
  onDone?: () => void;
}

const KIND_LABEL: Record<string, string> = { vlc: 'VLC', kodi: 'Kodi' };

/** "Play on…": send a channel to a saved VLC/Kodi player. */
const PlayOnMenu: React.FC<PlayOnMenuProps> = ({ contentId, title, onDone }) => {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [notice, setNotice] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);
  const { data: players = [], isLoading } = useRemotePlayers();
  const play = usePlayOnRemotePlayer();

  const send = async (id: number, name: string) => {
    setAnchor(null);
    try {
      await play.mutateAsync({ id, contentId, title });
      setNotice({ message: `Sent ${title} to ${name}.`, severity: 'success' });
      onDone?.();
    } catch (err) {
      setNotice({ message: err instanceof ApiError ? describeRemotePlayerError(err) : 'Could not reach the player.', severity: 'error' });
    }
  };

  return (
    <>
      <Button startIcon={<CastRoundedIcon />} onClick={(event) => setAnchor(event.currentTarget)} aria-haspopup="menu" aria-expanded={Boolean(anchor)} disabled={isLoading || play.isPending}>
        Play on…
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
        {players.length === 0 ? (
          <MenuItem component={RouterLink} to="/integrations" onClick={() => setAnchor(null)}>
            <ListItemText primary="Add a player" secondary="VLC or Kodi on your network, under Integrations" />
          </MenuItem>
        ) : (
          players.map((player) => (
            <MenuItem key={player.id} onClick={() => void send(player.id, player.name)}>
              <ListItemIcon><CastRoundedIcon fontSize="small" /></ListItemIcon>
              <ListItemText>{`${player.name} (${KIND_LABEL[player.kind] ?? player.kind})`}</ListItemText>
            </MenuItem>
          ))
        )}
      </Menu>
      <Snackbar open={notice !== null} autoHideDuration={5000} onClose={() => setNotice(null)}>
        <Alert severity={notice?.severity ?? 'success'} onClose={() => setNotice(null)}>{notice?.message}</Alert>
      </Snackbar>
    </>
  );
};

export default PlayOnMenu;
```

`frontend/src/components/player/ChannelPickerDialog.tsx`:

```tsx
import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Autocomplete, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useAcestreamChannels } from '../../hooks/useChannels';
import { usePlayOnRemotePlayer } from '../../hooks/useRemotePlayers';
import { useTVChannelCatalog } from '../../hooks/useTVChannels';
import { ApiError } from '../../services/apiErrors';
import type { RemotePlayer } from '../../services/remotePlayerService';
import { describeRemotePlayerError } from './playerCopy';

export interface ChannelPickerDialogProps {
  open: boolean;
  player: RemotePlayer | null;
  onClose: () => void;
}

interface PickerOption {
  key: string;
  label: string;
  secondary: string;
  contentId: string;
}

const useDebounced = (value: string, ms: number) => {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = window.setTimeout(() => setDebounced(value), ms);
    return () => window.clearTimeout(handle);
  }, [value, ms]);
  return debounced;
};

/** Pick a TV channel (best stream) or a raw stream and send it to a remote player. */
const ChannelPickerDialog: React.FC<ChannelPickerDialogProps> = ({ open, player, onClose }) => {
  const [mode, setMode] = useState<'tv' | 'streams'>('tv');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<PickerOption | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebounced(search, 300);
  const tv = useTVChannelCatalog({ search: debounced });
  const streams = useAcestreamChannels({ search: debounced || undefined, is_active: true, page: 1, page_size: 50 }, { enabled: open && mode === 'streams' });
  const play = usePlayOnRemotePlayer();

  const options = useMemo<PickerOption[]>(() => {
    if (mode === 'tv') {
      return (tv.data ?? [])
        .filter((channel) => channel.is_active && channel.acestream_channels.length > 0)
        .map((channel) => {
          const best = channel.acestream_channels[0];
          return { key: `tv-${channel.id}`, label: channel.name, secondary: `Best stream: ${best.name} · ${best.is_online ? 'Online' : best.is_online === false ? 'Offline' : 'Unchecked'}`, contentId: best.id };
        });
    }
    return (streams.data?.items ?? []).map((stream) => ({ key: `s-${stream.id}`, label: stream.name, secondary: `${stream.group || 'No group'} · ${stream.is_online ? 'Online' : stream.is_online === false ? 'Offline' : 'Unchecked'}`, contentId: stream.id }));
  }, [mode, tv.data, streams.data]);

  const submit = async () => {
    if (!player || !selected) return;
    setError(null);
    try {
      await play.mutateAsync({ id: player.id, contentId: selected.contentId, title: selected.label });
      setSelected(null);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? describeRemotePlayerError(err) : 'Could not reach the player.');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="channel-picker-title">
      <DialogTitle id="channel-picker-title">Send a channel to {player?.name ?? 'the player'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <ToggleButtonGroup exclusive size="small" value={mode} onChange={(_e, value: 'tv' | 'streams' | null) => { if (value) { setMode(value); setSelected(null); } }} aria-label="What to pick">
            <ToggleButton value="tv">TV channels</ToggleButton>
            <ToggleButton value="streams">Streams</ToggleButton>
          </ToggleButtonGroup>
          <Autocomplete
            options={options}
            value={selected}
            onChange={(_e, value) => setSelected(value)}
            inputValue={search}
            onInputChange={(_e, value) => setSearch(value)}
            getOptionLabel={(option) => option.label}
            isOptionEqualToValue={(a, b) => a.key === b.key}
            loading={mode === 'tv' ? tv.isLoading : streams.isLoading}
            renderOption={(props, option) => (
              <li {...props} key={option.key}>
                <Stack>
                  <Typography>{option.label}</Typography>
                  <Typography variant="caption" color="text.secondary">{option.secondary}</Typography>
                </Stack>
              </li>
            )}
            renderInput={(params) => <TextField {...params} label="Channel" placeholder="Type to search" />}
          />
          {error ? <Alert severity="error">{error}</Alert> : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!selected || play.isPending} onClick={() => void submit()}>
          Send to {player?.name ?? 'player'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ChannelPickerDialog;
```

`ChannelRowActions.tsx`: add `onPlayOn: (channel: AcestreamChannel) => void;` to `ChannelActionHandlers` and a menu item `{ label: 'Play on…', icon: <CastRoundedIcon fontSize="small" />, onClick: () => onPlayOn(channel) }` right after the TV item. `ChannelTable.tsx`: pass `onPlayOn` through. `AcestreamChannels.tsx`: `onPlayOn: (channel) => setPlayOnTarget({ contentId: channel.id, title: channel.name })`; render a small anchored menu — simplest: reuse `PlayOnMenu` inside a `Dialog` titled "Play on…" that opens when `playOnTarget` is set, or open the `StreamPlayerDialog`'s `extraActions` path. Choose: open the `StreamPlayerDialog` with `extraActions={<PlayOnMenu contentId=… title=… />}` for `onPlay`, and for `onPlayOn` render `<Dialog open><DialogTitle>Play on…</DialogTitle><DialogContent><PlayOnMenu … onDone={close} /></DialogContent></Dialog>`; the same `extraActions` prop is passed to every `StreamPlayerDialog` created in plan 2 (TV detail, TV list, Search) so the player dialog always offers "Play on…".

- [ ] **Step 4: Integrations page and sections**

`frontend/src/components/layout/navItems.tsx`: import `HubRoundedIcon from '@mui/icons-material/HubRounded'` and insert `{ text: 'Integrations', path: '/integrations', icon: <HubRoundedIcon />, section: 'System' }` before Settings. `App.tsx`: `<Route path="/integrations" element={<Integrations />} />`. `e2e/src/pages/app-shell.ts`: add `'Integrations'` to `NavLabel` and `Integrations: '/integrations'` to `NAV_ROUTES`.

`frontend/src/components/integrations/PublicAddressSection.tsx`:

```tsx
import React, { useEffect, useState } from 'react';
import { Alert, Button, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import { PUBLIC_URL_QUERY_KEY, usePublicUrl } from '../../hooks/useSystemServices';
import { configService } from '../../services/configService';
import { getErrorMessage } from '../../utils/errorUtils';

const SOURCE_LABEL = { setting: 'Setting', forwarded: 'Proxy headers', request: 'Request' } as const;

const WARNING_TEXT: Record<string, string> = {
  localhost: 'This address only works from this machine. Jellyfin, Plex and players on other devices need the server’s network address, for example http://192.168.1.10:8000.',
  'docker-internal': 'This looks like a Docker-internal address that other devices cannot reach. Use the host’s LAN address instead.',
  unset: 'No public address is set, so links use whatever address your browser used. Set one if other devices should reach this server.',
  proxied: 'The saved address differs from the one you are browsing from. Make sure /tuner/ is not behind proxy authentication (see the reverse-proxy guide).',
};

export interface PublicAddressSectionProps {
  notify: (message: string, severity: 'success' | 'error') => void;
}

/** Where tuners, remote players and copied links reach this server. */
const PublicAddressSection: React.FC<PublicAddressSectionProps> = ({ notify }) => {
  const queryClient = useQueryClient();
  const { data, isLoading } = usePublicUrl();
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const saved = data?.source === 'setting' ? data.url : '';

  useEffect(() => setValue(saved), [saved]);

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await configService.updatePublicBaseUrl(value.trim());
      notify(value.trim() ? 'Public address saved.' : 'Public address cleared.', 'success');
      await queryClient.invalidateQueries({ queryKey: PUBLIC_URL_QUERY_KEY });
      await queryClient.invalidateQueries({ queryKey: ['tuner'] });
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ContentSection id="public-address" title="Public address" description="The address other devices use to reach this server. It goes into tuner, player and copied links.">
      <Stack spacing={2}>
        <Typography variant="body2">
          Currently <strong>{isLoading ? '…' : data?.url}</strong>{data ? ` (${SOURCE_LABEL[data.source]})` : ''}
        </Typography>
        {(data?.warnings ?? []).map((warning) => (
          <Alert key={warning} severity="warning">{WARNING_TEXT[warning] ?? warning}</Alert>
        ))}
        <Stack component="form" direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'flex-start' }} onSubmit={(e: React.FormEvent) => void save(e)} aria-label="Public address form">
          <TextField size="small" fullWidth label="Public address" placeholder="http://192.168.1.10:8000" value={value} onChange={(e) => setValue(e.target.value)} inputProps={{ 'aria-label': 'Public address' }} helperText="Scheme and host, optionally a port. Leave empty to derive it from each request." />
          <Button type="submit" variant="contained" disabled={saving || value.trim() === saved}>Save</Button>
        </Stack>
      </Stack>
    </ContentSection>
  );
};

export default PublicAddressSection;
```

(Confirm `ContentSection` accepts an `id` prop; if not, wrap it in `<Box id="public-address">`.)

`frontend/src/components/integrations/WebPlayerSection.tsx`:

```tsx
import React from 'react';
import { Alert, Chip, List, ListItem, ListItemText, Stack, Typography } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import { usePlayerCapabilities, usePlayerSessions } from '../../hooks/usePlayer';

/** ffmpeg availability and what is playing in browsers right now. */
const WebPlayerSection: React.FC = () => {
  const { data: caps } = usePlayerCapabilities();
  const { data: sessions } = usePlayerSessions();
  const list = sessions?.sessions ?? [];
  return (
    <ContentSection title="Web player" description="Channels play in the browser through a small server-side conversion (video copied, audio re-encoded).">
      <Stack spacing={1.5}>
        {caps && !caps.ffmpeg_available ? (
          <Alert severity="warning">ffmpeg is not available on this server, so channels cannot play in the browser. Set FFMPEG_BINARY_PATH or use the bundled image.</Alert>
        ) : (
          <Typography variant="body2" color="text.secondary">
            ffmpeg {caps?.ffmpeg_path ? `at ${caps.ffmpeg_path}` : 'ready'} · up to {caps?.max_sessions ?? '…'} channels at once
          </Typography>
        )}
        {list.length === 0 ? (
          <Typography variant="body2">Nothing is playing right now.</Typography>
        ) : (
          <List dense>
            {list.map((session) => (
              <ListItem key={session.id} secondaryAction={<Chip size="small" label={session.state} />}>
                <ListItemText primary={session.content_id} secondary={`${session.viewers} viewer${session.viewers === 1 ? '' : 's'}${session.stats ? ` · ${session.stats.peers} peers` : ''}`} />
              </ListItem>
            ))}
          </List>
        )}
      </Stack>
    </ContentSection>
  );
};

export default WebPlayerSection;
```

`frontend/src/components/integrations/RemotePlayerDialog.tsx` (add/edit + Test connection):

```tsx
import React, { useEffect, useState } from 'react';
import { Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material';
import { useBaseUrls } from '../../hooks/useBaseUrls';
import { useCreateRemotePlayer, useTestRemotePlayer, useUpdateRemotePlayer } from '../../hooks/useRemotePlayers';
import { ApiError } from '../../services/apiErrors';
import type { RemotePlayer, RemotePlayerKind, RemotePlayerProbe } from '../../services/remotePlayerService';
import { getErrorMessage } from '../../utils/errorUtils';

export interface RemotePlayerDialogProps {
  open: boolean;
  player: RemotePlayer | null;          // null = add
  prefill?: { host: string; port: number; kind: RemotePlayerKind } | null;
  onClose: () => void;
  notify: (message: string, severity: 'success' | 'error') => void;
}

const describeProbe = (probe: RemotePlayerProbe): { severity: 'success' | 'warning' | 'error'; text: string } => {
  if (!probe.reachable) return { severity: 'error', text: `${probe.message} ${probe.hint ?? ''}`.trim() };
  if (!probe.authenticated) return { severity: 'warning', text: probe.hint ?? probe.message };
  const access = probe.tuner_access.allowed ? '' : ` This player (${probe.tuner_access.addresses.join(', ')}) is outside TUNER_ALLOWED_NETWORKS and will get 403 from the stream link: add its network or choose a stream link format that points at the engine or Acexy.`;
  return { severity: probe.tuner_access.allowed ? 'success' : 'warning', text: `Connected${probe.version ? ` (version ${probe.version})` : ''}.${access}` };
};

const RemotePlayerDialog: React.FC<RemotePlayerDialogProps> = ({ open, player, prefill, onClose, notify }) => {
  const [name, setName] = useState('');
  const [kind, setKind] = useState<RemotePlayerKind>('vlc');
  const [host, setHost] = useState('');
  const [port, setPort] = useState('8080');
  const [username, setUsername] = useState('kodi');
  const [password, setPassword] = useState('');
  const [baseUrlId, setBaseUrlId] = useState<number | ''>('');
  const [probe, setProbe] = useState<{ severity: 'success' | 'warning' | 'error'; text: string } | null>(null);
  const { data: baseUrls = [] } = useBaseUrls();
  const create = useCreateRemotePlayer();
  const update = useUpdateRemotePlayer();
  const test = useTestRemotePlayer();

  useEffect(() => {
    if (!open) return;
    setProbe(null);
    setPassword('');
    if (player) {
      setName(player.name); setKind(player.kind); setHost(player.host); setPort(String(player.port)); setUsername(player.username ?? 'kodi'); setBaseUrlId(player.base_url_id ?? '');
    } else {
      setName(''); setKind(prefill?.kind ?? 'vlc'); setHost(prefill?.host ?? ''); setPort(String(prefill?.port ?? 8080)); setUsername('kodi'); setBaseUrlId('');
    }
  }, [open, player, prefill]);

  const runTest = async () => {
    setProbe(null);
    try {
      const result = await test.mutateAsync({ kind, host: host.trim(), port: Number(port), username: kind === 'kodi' ? username : undefined, password: password || undefined, id: player?.id });
      setProbe(describeProbe(result));
    } catch (err) {
      setProbe({ severity: 'error', text: err instanceof ApiError ? err.message : getErrorMessage(err) });
    }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const body = { name: name.trim(), kind, host: host.trim(), port: Number(port), username: kind === 'kodi' ? username : null, base_url_id: baseUrlId === '' ? null : baseUrlId };
    try {
      if (player) {
        await update.mutateAsync({ id: player.id, data: { ...body, password: password || undefined, clear_base_url: baseUrlId === '' } });
        notify(`Saved ${body.name}.`, 'success');
      } else {
        await create.mutateAsync({ ...body, password: password || null });
        notify(`Added ${body.name}.`, 'success');
      }
      onClose();
    } catch (err) {
      notify(err instanceof ApiError && err.status === 409 ? `A player named "${body.name}" already exists.` : getErrorMessage(err), 'error');
    }
  };

  const valid = name.trim() && host.trim() && /^\d+$/.test(port);
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="remote-player-dialog-title">
      <form onSubmit={(e) => void submit(e)}>
        <DialogTitle id="remote-player-dialog-title">{player ? `Edit ${player.name}` : 'Add player'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} inputProps={{ 'aria-label': 'Name' }} fullWidth required />
            <FormControl fullWidth>
              <InputLabel id="remote-player-kind">Player</InputLabel>
              <Select labelId="remote-player-kind" label="Player" value={kind} onChange={(e) => setKind(e.target.value as RemotePlayerKind)}>
                <MenuItem value="vlc">VLC (desktop)</MenuItem>
                <MenuItem value="kodi">Kodi</MenuItem>
              </Select>
            </FormControl>
            <Stack direction="row" spacing={1}>
              <TextField label="Host" value={host} onChange={(e) => setHost(e.target.value)} inputProps={{ 'aria-label': 'Host' }} fullWidth required helperText="IP address or hostname on your network" />
              <TextField label="Port" value={port} onChange={(e) => setPort(e.target.value)} inputProps={{ 'aria-label': 'Port', inputMode: 'numeric' }} sx={{ width: 120 }} />
            </Stack>
            {kind === 'kodi' ? <TextField label="Username" value={username} onChange={(e) => setUsername(e.target.value)} fullWidth /> : null}
            <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} fullWidth helperText={player?.has_password ? 'Leave empty to keep the saved password.' : kind === 'vlc' ? 'The Lua HTTP password you set in VLC.' : 'From Kodi > Settings > Services > Control.'} />
            <FormControl fullWidth size="small">
              <InputLabel id="remote-player-link-format">Stream link format</InputLabel>
              <Select labelId="remote-player-link-format" label="Stream link format" value={baseUrlId} onChange={(e) => setBaseUrlId(e.target.value === '' ? '' : Number(e.target.value))}>
                <MenuItem value="">Server relay (recommended)</MenuItem>
                {baseUrls.map((entry) => <MenuItem key={entry.id} value={entry.id}>{entry.name}</MenuItem>)}
              </Select>
            </FormControl>
            {probe ? <Alert severity={probe.severity}>{probe.text}</Alert> : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void runTest()} disabled={!host.trim() || test.isPending}>{test.isPending ? <CircularProgress size={18} /> : 'Test connection'}</Button>
          <Button onClick={onClose} color="inherit">Cancel</Button>
          <Button type="submit" variant="contained" disabled={!valid || create.isPending || update.isPending}>{player ? 'Save' : 'Add player'}</Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default RemotePlayerDialog;
```

`frontend/src/components/integrations/FindPlayersDialog.tsx`:

```tsx
import React, { useEffect, useState } from 'react';
import { Alert, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, List, ListItem, ListItemText, Stack, TextField, Typography } from '@mui/material';
import { useScanDefault, useScanRemotePlayers } from '../../hooks/useRemotePlayers';
import type { RemotePlayerKind, ScanHit } from '../../services/remotePlayerService';
import { getErrorMessage } from '../../utils/errorUtils';

export interface FindPlayersDialogProps {
  open: boolean;
  onClose: () => void;
  onAdd: (prefill: { host: string; port: number; kind: RemotePlayerKind }) => void;
}

const FindPlayersDialog: React.FC<FindPlayersDialogProps> = ({ open, onClose, onAdd }) => {
  const { data: suggestion } = useScanDefault(open);
  const scan = useScanRemotePlayers();
  const [cidr, setCidr] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && suggestion?.cidr && !cidr) setCidr(suggestion.cidr);
  }, [open, suggestion, cidr]);

  const run = async () => {
    setError(null);
    try {
      await scan.mutateAsync({ cidr: cidr.trim(), ports: [8080] });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const hits: ScanHit[] = scan.data?.hosts ?? [];
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="find-players-title">
      <DialogTitle id="find-players-title">Find players</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">Looks for VLC and Kodi web interfaces on port 8080. {suggestion?.hint}</Typography>
          <Stack direction="row" spacing={1}>
            <TextField label="Network" value={cidr} onChange={(e) => setCidr(e.target.value)} placeholder="192.168.1.0/24" fullWidth inputProps={{ 'aria-label': 'Network' }} />
            <Button variant="contained" onClick={() => void run()} disabled={!cidr.trim() || scan.isPending}>{scan.isPending ? <CircularProgress size={18} /> : 'Scan'}</Button>
          </Stack>
          {error ? <Alert severity="error">{error}</Alert> : null}
          {scan.data ? (
            hits.length === 0 ? (
              <Alert severity="info">Nothing answered on port 8080 across {scan.data.scanned} addresses. Turn on the web interface in VLC (Preferences › Interface › Main interfaces › Web) or Kodi (Services › Control), then scan again.</Alert>
            ) : (
              <List dense>
                {hits.map((hit) => (
                  <ListItem key={`${hit.host}:${hit.port}`} secondaryAction={hit.kind === 'unknown' ? null : <Button size="small" onClick={() => onAdd({ host: hit.host, port: hit.port, kind: hit.kind })}>Add</Button>}>
                    <ListItemText primary={<Stack direction="row" spacing={1} alignItems="center"><span>{hit.host}:{hit.port}</span><Chip size="small" label={hit.kind === 'vlc' ? 'VLC' : hit.kind === 'kodi' ? 'Kodi' : 'Unknown'} /></Stack>} secondary={hit.hint} />
                  </ListItem>
                ))}
              </List>
            )
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions><Button onClick={onClose}>Close</Button></DialogActions>
    </Dialog>
  );
};

export default FindPlayersDialog;
```

`frontend/src/components/integrations/RemotePlayersSection.tsx`:

```tsx
import React, { useState } from 'react';
import { Box, Button, Chip, Grid, IconButton, Paper, Slider, Stack, Tooltip, Typography, useTheme } from '@mui/material';
import PauseRoundedIcon from '@mui/icons-material/PauseRounded';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import StopRoundedIcon from '@mui/icons-material/StopRounded';
import ContentSection from '../layout/ContentSection';
import RowActionsMenu from '../RowActionsMenu';
import { useConfirm } from '../ConfirmDialog';
import EmptyState from '../state/EmptyState';
import { useDeleteRemotePlayer, useRemotePlayerCommand, useRemotePlayerStatus, useRemotePlayers } from '../../hooks/useRemotePlayers';
import { ApiError } from '../../services/apiErrors';
import { remotePlayerService, type RemotePlayer, type RemotePlayerKind } from '../../services/remotePlayerService';
import { getErrorMessage } from '../../utils/errorUtils';
import { describeRemotePlayerError } from '../player/playerCopy';
import ChannelPickerDialog from '../player/ChannelPickerDialog';
import FindPlayersDialog from './FindPlayersDialog';
import RemotePlayerDialog from './RemotePlayerDialog';

export interface RemotePlayersSectionProps {
  notify: (message: string, severity: 'success' | 'error') => void;
}

const KIND_LABEL: Record<RemotePlayerKind, string> = { vlc: 'VLC', kodi: 'Kodi' };

const formatClock = (seconds: number | null) => {
  if (seconds === null || seconds === undefined) return '';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
};

interface PlayerCardProps {
  player: RemotePlayer;
  onEdit: () => void;
  onDelete: () => void;
  onSend: () => void;
  onTest: () => void;
  notify: RemotePlayersSectionProps['notify'];
}

const PlayerCard: React.FC<PlayerCardProps> = ({ player, onEdit, onDelete, onSend, onTest, notify }) => {
  const theme = useTheme();
  const { data: status, error } = useRemotePlayerStatus(player.id);
  const command = useRemotePlayerCommand();
  const run = async (cmd: 'pause' | 'resume' | 'stop' | 'volume', value?: number) => {
    try {
      await command.mutateAsync({ id: player.id, command: cmd, value });
    } catch (err) {
      notify(err instanceof ApiError ? describeRemotePlayerError(err) : getErrorMessage(err), 'error');
    }
  };
  const statusText = error
    ? error instanceof ApiError ? describeRemotePlayerError(error) : 'Unreachable'
    : status
      ? status.state === 'stopped' ? 'Idle' : `${status.state === 'playing' ? 'Playing' : 'Paused'}${status.title ? ` · ${status.title}` : ''}${status.position_s !== null ? ` · ${formatClock(status.position_s)}` : ''}`
      : 'Checking…';
  const tone = error ? 'error' : status?.state === 'playing' ? 'success' : 'default';
  return (
    <Paper variant="outlined" role="group" aria-label={`Player ${player.name}`} sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', gap: 1, borderColor: theme.appTokens.surface.border, backgroundColor: theme.appTokens.surface.raised }}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
        <Box>
          <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 600 }}>{player.name}</Typography>
          <Typography variant="body2" color="text.secondary">{player.host}:{player.port}</Typography>
        </Box>
        <Chip size="small" label={KIND_LABEL[player.kind]} />
      </Stack>
      <Typography variant="body2" role="status" color={tone === 'error' ? 'error.main' : tone === 'success' ? 'success.main' : 'text.secondary'}>{statusText}</Typography>
      <Stack direction="row" spacing={1} alignItems="center">
        {status?.state === 'playing' ? (
          <Tooltip title="Pause"><IconButton size="small" aria-label={`Pause ${player.name}`} onClick={() => void run('pause')}><PauseRoundedIcon /></IconButton></Tooltip>
        ) : (
          <Tooltip title="Resume"><span><IconButton size="small" aria-label={`Resume ${player.name}`} disabled={!status || status.state === 'stopped'} onClick={() => void run('resume')}><PlayArrowRoundedIcon /></IconButton></span></Tooltip>
        )}
        <Tooltip title="Stop"><span><IconButton size="small" aria-label={`Stop ${player.name}`} disabled={!status || status.state === 'stopped'} onClick={() => void run('stop')}><StopRoundedIcon /></IconButton></span></Tooltip>
        <Slider size="small" aria-label={`Volume ${player.name}`} value={status?.volume_pct ?? 0} min={0} max={200} sx={{ mx: 1, flex: 1 }} disabled={!status} onChangeCommitted={(_e, value) => void run('volume', Array.isArray(value) ? value[0] : value)} />
        <RowActionsMenu label={`More actions for ${player.name}`} actions={[
          { label: 'Send channel…', onClick: onSend },
          { label: 'Edit', onClick: onEdit },
          { label: 'Test connection', onClick: onTest },
          { label: 'Delete', danger: true, onClick: onDelete },
        ]} />
      </Stack>
    </Paper>
  );
};

/** Saved VLC/Kodi players with live status and transport controls. */
const RemotePlayersSection: React.FC<RemotePlayersSectionProps> = ({ notify }) => {
  const { data: players = [], isLoading } = useRemotePlayers();
  const remove = useDeleteRemotePlayer();
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [editing, setEditing] = useState<RemotePlayer | null>(null);
  const [adding, setAdding] = useState(false);
  const [prefill, setPrefill] = useState<{ host: string; port: number; kind: RemotePlayerKind } | null>(null);
  const [finding, setFinding] = useState(false);
  const [sending, setSending] = useState<RemotePlayer | null>(null);

  const handleDelete = async (player: RemotePlayer) => {
    const ok = await confirm({ title: `Delete ${player.name}?`, body: 'The player is removed from this list. Nothing changes on the player itself.', confirmLabel: 'Delete', danger: true });
    if (!ok) return;
    try {
      await remove.mutateAsync(player.id);
      notify(`Deleted ${player.name}.`, 'success');
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    }
  };

  const handleTest = async (player: RemotePlayer) => {
    try {
      const probe = await remotePlayerService.testSaved(player.id);
      notify(probe.reachable && probe.authenticated ? `${player.name} answered${probe.version ? ` (version ${probe.version})` : ''}.` : probe.hint ?? probe.message, probe.reachable && probe.authenticated ? 'success' : 'error');
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    }
  };

  return (
    <ContentSection title="Remote players" description="VLC or Kodi on your network. Send any channel there and control playback from here." actions={
      <Stack direction="row" spacing={1}>
        <Button variant="outlined" size="small" onClick={() => setFinding(true)}>Find players</Button>
        <Button variant="contained" size="small" onClick={() => { setPrefill(null); setAdding(true); }}>Add player</Button>
      </Stack>
    }>
      {isLoading ? <Typography variant="body2">Loading players…</Typography> : players.length === 0 ? (
        <EmptyState title="No players yet" description="Add VLC or Kodi from a device on this network, or scan for them." />
      ) : (
        <Grid container spacing={2}>
          {players.map((player) => (
            <Grid item xs={12} md={6} lg={4} key={player.id}>
              <PlayerCard player={player} notify={notify} onEdit={() => setEditing(player)} onDelete={() => void handleDelete(player)} onSend={() => setSending(player)} onTest={() => void handleTest(player)} />
            </Grid>
          ))}
        </Grid>
      )}
      <RemotePlayerDialog open={adding || editing !== null} player={editing} prefill={prefill} onClose={() => { setAdding(false); setEditing(null); }} notify={notify} />
      <FindPlayersDialog open={finding} onClose={() => setFinding(false)} onAdd={(hit) => { setFinding(false); setPrefill(hit); setAdding(true); }} />
      <ChannelPickerDialog open={sending !== null} player={sending} onClose={() => setSending(null)} />
      {confirmDialog}
    </ContentSection>
  );
};

export default RemotePlayersSection;
```

`frontend/src/pages/Integrations.tsx`:

```tsx
import React, { useState } from 'react';
import { Alert, Box, Snackbar } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import StatusLine from '../components/StatusLine';
import PublicAddressSection from '../components/integrations/PublicAddressSection';
import WebPlayerSection from '../components/integrations/WebPlayerSection';
import RemotePlayersSection from '../components/integrations/RemotePlayersSection';
import { usePublicUrl } from '../hooks/useSystemServices';
import { usePlayerSessions } from '../hooks/usePlayer';
import { useRemotePlayers } from '../hooks/useRemotePlayers';

type Feedback = { message: string; severity: 'success' | 'error' } | null;

/** Play channels in the browser, on players in your network, and (plan 4) in Jellyfin or Plex. */
const Integrations: React.FC = () => {
  const [feedback, setFeedback] = useState<Feedback>(null);
  const notify = (message: string, severity: 'success' | 'error') => setFeedback({ message, severity });
  const { data: publicUrl } = usePublicUrl();
  const { data: players } = useRemotePlayers();
  const { data: sessions } = usePlayerSessions();

  return (
    <Box>
      <PageHeader title="Integrations" subtitle="Play channels in the browser, on players in your network, and in Jellyfin or Plex." />
      <StatusLine
        aria-label="Integration summary"
        items={[
          { label: 'Public address', value: publicUrl?.url ?? '…', tone: publicUrl && publicUrl.warnings.length > 0 ? 'warning' : 'default' },
          { label: 'Players', value: players ? String(players.length) : '…' },
          { label: 'Active streams', value: sessions ? String(sessions.sessions.length) : '…' },
        ]}
      />
      <PublicAddressSection notify={notify} />
      <WebPlayerSection />
      <RemotePlayersSection notify={notify} />
      <Snackbar open={feedback !== null} autoHideDuration={5000} onClose={() => setFeedback(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={() => setFeedback(null)} severity={feedback?.severity ?? 'success'} variant="filled" sx={{ width: '100%' }}>{feedback?.message}</Alert>
      </Snackbar>
    </Box>
  );
};

export default Integrations;
```

- [ ] **Step 5: Run**

Run: `cd frontend && npm test -- PlayOnMenu.test.tsx ChannelPickerDialog.test.tsx Integrations.test.tsx routes.test.tsx ChannelRowActions.test.tsx ChannelTable.test.tsx ChannelCardList.test.tsx AcestreamChannelsPage.test.tsx StreamPlayerDialog.test.tsx && npm run lint -- --max-warnings=0 && npm run typecheck`
Expected: PASS. Adjust `Integrations.test.tsx` mocks to whatever hooks the sections actually import (the test lists them all).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Integrations.tsx frontend/src/components/integrations frontend/src/components/player/PlayOnMenu.tsx frontend/src/components/player/ChannelPickerDialog.tsx frontend/src/components/player/playerCopy.ts frontend/src/hooks/usePlayer.ts frontend/src/services/playerService.ts frontend/src/components/layout/navItems.tsx frontend/src/App.tsx frontend/src/components/channels/ChannelRowActions.tsx frontend/src/components/ChannelTable.tsx frontend/src/pages/AcestreamChannels.tsx frontend/src/pages/TVChannelDetail.tsx frontend/src/pages/TVChannels.tsx frontend/src/pages/Search.tsx frontend/src/__tests__ e2e/src/pages/app-shell.ts
git commit -m "feat(frontend): Integrations page with public address, web player and remote players; Play on… everywhere"
```

---

### Task 7: Contracts, docs and full verification

- [ ] **Step 1: Contract tests and quick profile**

Extend `backend/tests/contracts/test_integrations_contracts.py` (created in plan 2) with: `RemotePlayerCreate` validation (kind enum, port bounds), exact key sets for `GET /api/v1/remote-players` items (`{"id","name","kind","host","port","username","base_url_id","has_password","created_at","updated_at"}`), `POST /api/v1/remote-players/test` (`{"reachable","authenticated","version","message","hint","tuner_access"}`), `GET /api/v1/remote-players/scan/default` (`{"cidr","hint"}`), and the error codes `REMOTE_PLAYER_HOST_FORBIDDEN`, `SCAN_CIDR_NOT_PRIVATE`. Use `alembic_client` and the MockTransport swap from `test_remote_players_api.py`.

- [ ] **Step 2: Docs**

Create `wiki/Remote-Players.md`: what it does; VLC setup (Tools › Preferences › Show settings: All › Interface › Main interfaces › Web, then Lua › Lua HTTP › Password; allow the firewall prompt; the app needs the password), Kodi setup (Settings › Services › Control: allow remote control via HTTP, from other systems, set a password), "Find players" (scans port 8080 on a private network; type the network when the app cannot guess it, e.g. on Docker Desktop), the stream link format choice (server relay needs only port 8000 and `TUNER_ALLOWED_NETWORKS`; Acexy/engine formats need those ports published), Tailscale note (100.64/10 is in the default allowlist), the guided error messages, and that passwords are stored unencrypted in the app database. Add a Remote players paragraph to `README.md` and link the page from `wiki/Home.md` (or the wiki index used by `scripts/ci/publish_wiki.sh`). CLAUDE.md: remote players domain (drivers, service, scan, endpoints) and the Integrations page.

- [ ] **Step 3: Regenerate and run**

```bash
backend/venv/bin/python backend/scripts/dump_openapi.py && cd frontend && npm run codegen && cd ..
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests --ignore=backend/tests/docker
cd frontend && npm run lint -- --max-warnings=0 && npm run typecheck && CI=true npm test -- --watch=false && npm run build && cd ..
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/publish_wiki.sh --dry-run
```
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/openapi.json frontend/src/types/api-generated.ts backend/tests/contracts/test_integrations_contracts.py wiki/Remote-Players.md wiki/Home.md README.md CLAUDE.md
git commit -m "docs(remote-players): guide, contracts and regenerated API types"
```

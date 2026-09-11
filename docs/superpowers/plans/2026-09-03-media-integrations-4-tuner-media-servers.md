# Media Integrations, Plan 4: HDHomeRun Tuner, Jellyfin/Plex Sync, Docs and e2e — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the curated TV channels as an HDHomeRun-style tuner (plus an M3U/XMLTV pair) that Jellyfin and Plex consume, register and refresh Jellyfin automatically from the UI, give Plex users paste-ready instructions and an optional token-driven guide refresh, and finish the feature set with docs, contract tests and the e2e journey.

**Architecture:** `TunerService` builds the lineup (best stream per active TV channel, collision-free GuideNumbers, cap, fingerprints) and the two XMLTV/M3U variants on top of a refactored `EPGService`; `tuner.py`'s `hdhr_router` gains the tuner routes and its token-gated `router` gains settings/status. `media_servers/` holds a `JellyfinClient`, a `PlexClient` and `MediaServerService` (connect/test/refresh/status/disconnect) with a 10-minute fingerprint-driven sync job. The frontend adds the Media servers section to the Integrations page and the allowlist diagnostics to the Public address section.

**Tech Stack:** FastAPI, httpx (`MockTransport` fakes for Jellyfin/Plex), APScheduler job, SQLAlchemy; React/MUI/react-query; Playwright.

**Spec:** `docs/superpowers/specs/2026-09-03-media-integrations-design.md` sections 4.4, 7, 8, 10, 11. Plans 1-3 complete: `tuner.py` (`hdhr_router` with `/tuner/stream/{id}.ts` and the catch-all; empty `router`), `require_tuner_network`/`TunerNetworkGate` (`get_tuner_gate()`, `recent_denials()`, `classify_source()`, `allowed_networks`), `resolve_public_base_url`, `sort_streams_curated`, `MediaServer` model, `validate_lan_target`, `player_service.capabilities()`, the Integrations page with `notify`.

## Global Constraints

- Backend tests from the repo root with `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/<file>`; `alembic_client`/`alembic_db_session` for the `media_servers` table.
- Tuner routes are token-free and allowlist-gated (`hdhr_router`); `/api/v1/tuner/settings` and `/api/v1/tuner/status` are token-gated. The catch-all `/tuner/{path:path}` stays the last route in `tuner.py`. DB-touching handlers are sync `def`.
- Lineup rules: `TVChannel.is_active` with ≥1 stream, curated order; best stream = `sort_streams_curated(...)[0]`; `GuideNumber = channel_number` when set and unclaimed else `fallback_base + tv_channel.id` with `fallback_base = max(1000, max(explicit)+1)`; cap `tuner_max_channels` default 450 (1..1000); `discover.json` values exactly: `Manufacturer "Silicondust"`, `ModelNumber "HDTC-2US"`, `FirmwareName "hdhomeruntc_atsc"`, `FirmwareVersion "20240101"`, `DeviceAuth ""`, `BaseURL {public}/tuner`, `LineupURL {public}/tuner/lineup.json`.
- XMLTV for tuners: `<channel id="{GuideNumber}">` with three `<display-name>`s ("N Name", "N", "Name") and `<icon>`, programmes keyed by GuideNumber, uncompressed; `/api/v1/epg/xml` output stays byte-for-byte identical.
- Jellyfin: header `Authorization: MediaBrowser Token="<key>", Client="acestream-scraper", Device="acestream-scraper", DeviceId="<tuner_device_id>", Version="<app version>"`; PascalCase bodies; HDHR tuner host `{Type:"hdhomerun", Url:"{public}/tuner", FriendlyName, TunerCount:0, AllowHWTranscoding:false, AllowStreamSharing:true, ImportFavoritesOnly:false}`; provider `{Type:"xmltv", Path:"{public}/tuner/guide.xml", EnableAllTuners:false, EnabledTuners:[tunerId]}`; refresh via `GET /ScheduledTasks` → `Key == "RefreshGuide"` → `POST /ScheduledTasks/Running/{Id}`.
- Error mapping: `MEDIA_SERVER_UNREACHABLE`/`MEDIA_SERVER_AUTH`/`MEDIA_SERVER_ERROR` → 502 with upstream status in `context`; `MEDIA_SERVER_NOT_CONNECTED` → 409; `MEDIA_SERVER_URL_FORBIDDEN` → 422. `last_sync_status` ∈ {ok, error, never, manual}.
- Frontend rules as in plans 2-3 (two visible actions per card: Refresh now + Connect/Disconnect; Edit/Test/Delete in `RowActionsMenu`; `useConfirm` on Delete and on Jellyfin Disconnect only; plain copy).
- Commit trailers: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_01NCvyzQfF1uXiozTEGgDvPM`. Branch `feature/media-integrations`. Never commit `docs/superpowers/` or `.superpowers/`.

---

### Task 1: Tuner settings, DeviceID and lineup allocation

**Files:**
- Modify: `backend/app/repositories/settings_repository.py`
- Create: `backend/app/services/tuner_service.py`
- Test: `backend/tests/test_tuner_service.py`

**Interfaces:**
- Produces: settings keys `TUNER_DEVICE_ID`, `TUNER_FRIENDLY_NAME` (default `AceStream Scraper`), `TUNER_COUNT` (`4`), `TUNER_MAX_CHANNELS` (`450`), `TUNER_ONLY_ONLINE` (`false`); `hdhr_device_id_valid(device_id) -> bool`, `generate_hdhr_device_id() -> str`; `TunerSettings` dataclass; `LineupEntry(guide_number, guide_name, content_id, tv_channel_id, epg_id, epg_source_id, logo_url, category, requested_number)`; `Lineup(entries, renumbered: list[Renumbered], overflow: int)`; `TunerService(db)` with `settings() -> TunerSettings`, `update_settings(**fields)`, `device_id() -> str` (generated and persisted once), `build_lineup() -> Lineup`, `lineup_fingerprint(lineup) -> str`, `guide_fingerprint() -> str`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_tuner_service.py`:

```python
"""Tuner settings, HDHomeRun DeviceID checksum and lineup allocation (spec 7.2)."""
import uuid

import pytest

from app.services.tuner_service import TunerService, generate_hdhr_device_id, hdhr_device_id_valid


def _tv(db, name, number=None, active=True, streams=()):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name=name, channel_number=number, is_active=active, epg_id=f"{name}.epg", logo_url=f"http://logo/{name}.png", category="Sports")
    db.add(tv)
    db.flush()
    for idx, (online, logo) in enumerate(streams):
        db.add(AcestreamChannel(id=uuid.uuid4().hex + "0" * 8, name=f"{name} feed {idx}", is_online=online, logo=logo, is_active=True, tv_channel_id=tv.id))
    db.commit()
    return tv


@pytest.mark.parametrize("device_id", ["10E1F2F3", "1234567A"])
def test_known_valid_ids(device_id):
    # 1234567A: nibbles 1,2,3,4,5,6,7,A -> lookup[1]^2^lookup[3]^4^lookup[5]^6^lookup[7]^A = 5^2^6^4^C^6^B^A = 0
    assert hdhr_device_id_valid(device_id) is True


def test_generated_ids_are_valid_and_unique():
    ids = {generate_hdhr_device_id() for _ in range(50)}
    assert len(ids) == 50
    assert all(len(i) == 8 and hdhr_device_id_valid(i) for i in ids)
    assert not hdhr_device_id_valid("00000001")


def test_settings_defaults_and_persisted_device_id(db_session):
    svc = TunerService(db_session)
    settings = svc.settings()
    assert (settings.friendly_name, settings.tuner_count, settings.max_channels, settings.only_online) == ("AceStream Scraper", 4, 450, False)
    first = svc.device_id()
    assert hdhr_device_id_valid(first)
    assert TunerService(db_session).device_id() == first
    svc.update_settings(friendly_name="Living room", tuner_count=2, max_channels=10, only_online=True)
    assert svc.settings().tuner_count == 2 and svc.settings().only_online is True


def test_lineup_best_stream_numbers_and_renumbering(db_session):
    _tv(db_session, "Explicit 5", number=5, streams=[(False, None), (True, "logo")])
    _tv(db_session, "Second explicit 5", number=5, streams=[(True, None)])
    seven = _tv(db_session, "No number", streams=[(True, None)])
    _tv(db_session, "Inactive", number=9, active=False, streams=[(True, None)])
    _tv(db_session, "Empty", number=10)
    lineup = TunerService(db_session).build_lineup()
    by_name = {e.guide_name: e for e in lineup.entries}
    assert list(by_name) == ["Explicit 5", "Second explicit 5", "No number"]
    assert by_name["Explicit 5"].guide_number == "5"
    assert by_name["Explicit 5"].content_id.endswith("0" * 8) and by_name["Explicit 5"].content_id != ""
    # best stream = online + logo
    from app.models.models import AcestreamChannel
    best = db_session.query(AcestreamChannel).filter(AcestreamChannel.id == by_name["Explicit 5"].content_id).one()
    assert best.is_online and best.logo == "logo"
    base = max(1000, 5 + 1)
    assert by_name["Second explicit 5"].guide_number != "5"
    assert by_name["No number"].guide_number == str(base + seven.id)
    assert len({e.guide_number for e in lineup.entries}) == len(lineup.entries)
    assert [(r.name, r.requested_number) for r in lineup.renumbered] == [("Second explicit 5", 5)]


def test_lineup_cap_and_only_online(db_session):
    for i in range(3):
        _tv(db_session, f"C{i}", number=i + 1, streams=[(i != 1, None)])
    svc = TunerService(db_session)
    svc.update_settings(max_channels=2)
    lineup = svc.build_lineup()
    assert [e.guide_name for e in lineup.entries] == ["C0", "C1"] and lineup.overflow == 1
    svc.update_settings(max_channels=450, only_online=True)
    assert [e.guide_name for e in svc.build_lineup().entries] == ["C0", "C2"]


def test_fingerprints_change_with_lineup_and_epg_sources(db_session):
    from datetime import datetime, timezone
    from app.models.models import EPGSource
    svc = TunerService(db_session)
    lineup = svc.build_lineup()
    empty = svc.lineup_fingerprint(lineup)
    _tv(db_session, "New", number=1, streams=[(True, None)])
    assert svc.lineup_fingerprint(svc.build_lineup()) != empty
    g0 = svc.guide_fingerprint()
    source = EPGSource(url="http://x", name="x", enabled=True, last_updated=datetime(2026, 1, 1, tzinfo=timezone.utc))
    db_session.add(source); db_session.commit()
    g1 = svc.guide_fingerprint()
    assert g1 != g0
    source.last_error = "boom"; db_session.commit()
    assert svc.guide_fingerprint() == g0  # failed sources are ignored
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_service.py`
Expected: FAIL.

- [ ] **Step 3: Settings keys**

In `SettingsRepository` add keys and defaults:

```python
    TUNER_DEVICE_ID = 'tuner_device_id'
    TUNER_FRIENDLY_NAME = 'tuner_friendly_name'
    TUNER_COUNT = 'tuner_count'
    TUNER_MAX_CHANNELS = 'tuner_max_channels'
    TUNER_ONLY_ONLINE = 'tuner_only_online'
    ...
    DEFAULT_TUNER_DEVICE_ID = ''
    DEFAULT_TUNER_FRIENDLY_NAME = 'AceStream Scraper'
    DEFAULT_TUNER_COUNT = '4'
    DEFAULT_TUNER_MAX_CHANNELS = '450'
    DEFAULT_TUNER_ONLY_ONLINE = 'false'
```

(no `setup_defaults` entries needed: `get_setting` falls back to the `DEFAULT_` attributes; the device id is generated on first use by the service.)

- [ ] **Step 4: Service**

Create `backend/app/services/tuner_service.py`:

```python
"""HDHomeRun-style tuner lineup and settings (spec 7.2)."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import EPGSource, TVChannel
from app.repositories.channel_repository import ChannelRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.stream_ranking import sort_streams_curated

_LOOKUP = [0xA, 0x5, 0xF, 0x6, 0x7, 0xC, 0x1, 0xB, 0x9, 0x2, 0x8, 0xD, 0x4, 0x3, 0xE, 0x0]


def hdhr_device_id_valid(device_id: str) -> bool:
    """libhdhomerun's nibble checksum: odd positions (MSB first) go through the lookup table."""
    if len(device_id) != 8:
        return False
    try:
        value = int(device_id, 16)
    except ValueError:
        return False
    checksum = 0
    for position in range(7, -1, -1):
        nibble = (value >> (position * 4)) & 0xF
        checksum ^= _LOOKUP[nibble] if position % 2 == 1 else nibble
    return checksum == 0


def generate_hdhr_device_id() -> str:
    while True:
        value = secrets.randbits(28) << 4  # seven random nibbles, last nibble computed
        checksum = 0
        for position in range(7, 0, -1):
            nibble = (value >> (position * 4)) & 0xF
            checksum ^= _LOOKUP[nibble] if position % 2 == 1 else nibble
        device_id = f"{value | checksum:08X}"
        if device_id[0] != "0" and hdhr_device_id_valid(device_id):
            return device_id


@dataclass
class TunerSettings:
    friendly_name: str
    tuner_count: int
    max_channels: int
    only_online: bool


@dataclass
class LineupEntry:
    guide_number: str
    guide_name: str
    content_id: str
    tv_channel_id: int
    epg_id: Optional[str]
    epg_source_id: Optional[int]
    logo_url: Optional[str]
    category: Optional[str]
    requested_number: Optional[int]


@dataclass
class Renumbered:
    tv_channel_id: int
    name: str
    requested_number: int
    assigned_number: int


@dataclass
class Lineup:
    entries: List[LineupEntry] = field(default_factory=list)
    renumbered: List[Renumbered] = field(default_factory=list)
    overflow: int = 0


class TunerService:
    def __init__(self, db: Session):
        self.db = db
        self.settings_repo = SettingsRepository(db)

    # --- settings -----------------------------------------------------------
    def settings(self) -> TunerSettings:
        repo = self.settings_repo
        return TunerSettings(
            friendly_name=repo.get_setting(SettingsRepository.TUNER_FRIENDLY_NAME) or SettingsRepository.DEFAULT_TUNER_FRIENDLY_NAME,
            tuner_count=int(repo.get_setting(SettingsRepository.TUNER_COUNT) or SettingsRepository.DEFAULT_TUNER_COUNT),
            max_channels=int(repo.get_setting(SettingsRepository.TUNER_MAX_CHANNELS) or SettingsRepository.DEFAULT_TUNER_MAX_CHANNELS),
            only_online=str(repo.get_setting(SettingsRepository.TUNER_ONLY_ONLINE) or "false").lower() in ("true", "1"),
        )

    def update_settings(self, *, friendly_name: Optional[str] = None, tuner_count: Optional[int] = None,
                        max_channels: Optional[int] = None, only_online: Optional[bool] = None) -> TunerSettings:
        repo = self.settings_repo
        if friendly_name is not None:
            repo.set_setting(SettingsRepository.TUNER_FRIENDLY_NAME, friendly_name.strip() or SettingsRepository.DEFAULT_TUNER_FRIENDLY_NAME, "Tuner name shown in Jellyfin/Plex")
        if tuner_count is not None:
            repo.set_setting(SettingsRepository.TUNER_COUNT, str(max(1, min(16, int(tuner_count)))), "Concurrent tuner streams advertised")
        if max_channels is not None:
            repo.set_setting(SettingsRepository.TUNER_MAX_CHANNELS, str(max(1, min(1000, int(max_channels)))), "Maximum channels in the tuner lineup")
        if only_online is not None:
            repo.set_setting(SettingsRepository.TUNER_ONLY_ONLINE, "true" if only_online else "false", "Hide channels whose streams are all offline")
        return self.settings()

    def device_id(self) -> str:
        current = (self.settings_repo.get_setting(SettingsRepository.TUNER_DEVICE_ID) or "").strip().upper()
        if hdhr_device_id_valid(current):
            return current
        generated = generate_hdhr_device_id()
        self.settings_repo.set_setting(SettingsRepository.TUNER_DEVICE_ID, generated, "HDHomeRun device id advertised to Jellyfin/Plex")
        return generated

    # --- lineup -------------------------------------------------------------
    def build_lineup(self) -> Lineup:
        settings = self.settings()
        channels: List[TVChannel] = ChannelRepository(self.db).get_playlist_tv_channels()
        candidates = []
        for tv in channels:
            streams = [s for s in tv.acestream_channels if s.id]
            if not streams:
                continue
            if settings.only_online and not any(s.is_online for s in streams):
                continue
            candidates.append((tv, sort_streams_curated(streams)[0]))

        explicit = [tv.channel_number for tv, _ in candidates if tv.channel_number is not None]
        fallback_base = max(1000, (max(explicit) if explicit else 0) + 1)
        taken: set = set()
        lineup = Lineup()
        for tv, best in candidates:
            requested = tv.channel_number
            if requested is not None and requested not in taken:
                number = requested
            else:
                number = fallback_base + tv.id
                if requested is not None:
                    lineup.renumbered.append(Renumbered(tv_channel_id=tv.id, name=tv.name, requested_number=requested, assigned_number=number))
            taken.add(number)
            lineup.entries.append(LineupEntry(
                guide_number=str(number), guide_name=tv.name, content_id=best.id, tv_channel_id=tv.id,
                epg_id=tv.epg_id, epg_source_id=tv.epg_source_id, logo_url=tv.logo_url or best.logo, category=tv.category,
                requested_number=requested,
            ))
        if len(lineup.entries) > settings.max_channels:
            lineup.overflow = len(lineup.entries) - settings.max_channels
            lineup.entries = lineup.entries[: settings.max_channels]
        return lineup

    @staticmethod
    def lineup_fingerprint(lineup: Lineup) -> str:
        digest = hashlib.sha256()
        for entry in lineup.entries:
            digest.update(f"{entry.guide_number}|{entry.guide_name}|{entry.content_id}\n".encode("utf-8"))
        return digest.hexdigest()

    def guide_fingerprint(self) -> str:
        rows = (
            self.db.query(EPGSource.id, EPGSource.last_updated)
            .filter(EPGSource.enabled == True, EPGSource.last_error.is_(None))  # noqa: E712
            .order_by(EPGSource.id)
            .all()
        )
        digest = hashlib.sha256()
        for source_id, last_updated in rows:
            digest.update(f"{source_id}|{last_updated.isoformat() if last_updated else ''}\n".encode("utf-8"))
        return digest.hexdigest()
```

- [ ] **Step 5: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_service.py backend/tests/test_config.py`
Expected: PASS. (`get_playlist_tv_channels()` orders by number NULLs last then name; the test's expected order relies on that.)

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories/settings_repository.py backend/app/services/tuner_service.py backend/tests/test_tuner_service.py
git commit -m "feat(tuner): settings, HDHomeRun device id and lineup allocation"
```

---

### Task 2: EPG export refactor and the tuner guide/playlist builders

**Files:**
- Modify: `backend/app/services/epg_service.py:363-511`
- Modify: `backend/app/services/tuner_service.py` (add builders)
- Test: `backend/tests/test_tuner_exports.py`, `backend/tests/test_epg.py` (byte-identical guard)

**Interfaces:**
- Produces on `EPGService`: `generate_epg_xml(search_term=None, favorites_only=False, days_back=1, days_forward=7, tv_channel_ids=None)`; helpers `epg_channel_lookup(tv_channels) -> dict[(source_id, xml_id), EPGChannel]`, `programs_in_window(epg_channel_ids, days_back=1, days_forward=7) -> dict[int, list[EPGProgram]]`, `programme_xml_lines(program, channel_id) -> list[str]`.
- On `TunerService`: `build_guide_xml(lineup, days_back=1, days_forward=7) -> str` (numeric ids), `build_playlist_m3u(lineup, public_base_url) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_tuner_exports.py`:

```python
import uuid
from datetime import datetime, timedelta, timezone

from app.services.epg_service import EPGService
from app.services.tuner_service import TunerService


def _seed(db):
    from app.models.models import AcestreamChannel, EPGChannel, EPGProgram, EPGSource, TVChannel
    source = EPGSource(url="http://epg", name="epg", enabled=True)
    db.add(source); db.flush()
    epg_channel = EPGChannel(epg_source_id=source.id, channel_xml_id="DAZN LaLiga HD", name="DAZN", icon_url="http://icon")
    db.add(epg_channel); db.flush()
    now = datetime.now(timezone.utc)
    db.add(EPGProgram(epg_channel_id=epg_channel.id, start_time=now, end_time=now + timedelta(hours=1), title="Match & More", description="d"))
    tv = TVChannel(name="DAZN 1", channel_number=12, epg_id="DAZN LaLiga HD", epg_source_id=source.id, logo_url="http://logo", category="Sports", is_active=True)
    db.add(tv); db.flush()
    stream = AcestreamChannel(id="a" * 40, name="DAZN feed", is_online=True, is_active=True, tv_channel_id=tv.id)
    db.add(stream); db.commit()
    return tv


def test_guide_xml_uses_guide_numbers_and_three_display_names(db_session):
    _seed(db_session)
    svc = TunerService(db_session)
    xml = svc.build_guide_xml(svc.build_lineup())
    assert '<channel id="12">' in xml
    assert '<display-name>12 DAZN 1</display-name>' in xml and '<display-name>12</display-name>' in xml and '<display-name>DAZN 1</display-name>' in xml
    assert '<icon src="http://logo" />' in xml
    assert 'channel="12"' in xml and '<title>Match &amp; More</title>' in xml
    assert "DAZN LaLiga HD" not in xml


def test_playlist_m3u_uses_relay_urls_and_tvg_attributes(db_session):
    _seed(db_session)
    svc = TunerService(db_session)
    m3u = svc.build_playlist_m3u(svc.build_lineup(), "http://scraper.lan:8000")
    lines = m3u.strip().split("\n")
    assert lines[0] == "#EXTM3U"
    assert lines[1] == '#EXTINF:-1 tvg-id="DAZN LaLiga HD" tvg-chno="12" tvg-name="DAZN 1" tvg-logo="http://logo" group-title="Sports",DAZN 1'
    assert lines[2] == "http://scraper.lan:8000/tuner/stream/" + "a" * 40 + ".ts"


def test_generate_epg_xml_restricts_to_ids_and_stays_identical_without(db_session):
    tv = _seed(db_session)
    svc = EPGService(db_session)
    full = svc.generate_epg_xml()
    assert svc.generate_epg_xml(tv_channel_ids=[tv.id]) == full
    assert '<channel id="DAZN LaLiga HD">' in svc.generate_epg_xml(tv_channel_ids=[tv.id])
    assert "<channel " not in svc.generate_epg_xml(tv_channel_ids=[tv.id + 999])
```

Append to `backend/tests/test_epg.py` (inside the existing XML test class or at module level):

```python
def test_epg_xml_output_unchanged_by_refactor(client, seed_epg_programs, seed_tv_channels, db_session):
    """Guard: the tuner refactor extracts helpers but must not change /api/v1/epg/xml."""
    from app.services.epg_service import EPGService
    first = client.get("/api/v1/epg/xml").text
    assert first == EPGService(db_session).generate_epg_xml()
    assert first.startswith('<?xml version="1.0" encoding="utf-8" ?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n<tv generator-info-name="Acestream Scraper EPG Generator"')
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_exports.py`
Expected: FAIL.

- [ ] **Step 3: Refactor `generate_epg_xml`**

Replace the body of `generate_epg_xml` in `epg_service.py` with an equivalent that uses three new methods (same output, same ordering, same escaping):

```python
    def generate_epg_xml(self, search_term: Optional[str] = None, favorites_only: bool = False,
                         days_back: int = 1, days_forward: int = 7,
                         tv_channel_ids: Optional[List[int]] = None) -> str:
        """XMLTV for TV channels with EPG data. ``tv_channel_ids`` restricts the
        export (tuner use); None keeps the historical output byte-for-byte."""
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8" ?>',
            '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
            '<tv generator-info-name="Acestream Scraper EPG Generator" generator-info-url="https://github.com/pipepito/acestream-scraper">'
        ]
        tv_channels_query = self.db.query(TVChannel).filter(TVChannel.epg_id.isnot(None))
        if search_term:
            tv_channels_query = tv_channels_query.filter(TVChannel.name.ilike(f"%{search_term}%"))
        if favorites_only:
            tv_channels_query = tv_channels_query.filter(TVChannel.is_favorite == True)
        if tv_channel_ids is not None:
            tv_channels_query = tv_channels_query.filter(TVChannel.id.in_(list(tv_channel_ids)))
        sorted_channels = sorted(tv_channels_query.all(), key=lambda c: (c.channel_number is None, c.channel_number or 0, c.name.lower()))
        epg_lookup = self.epg_channel_lookup(sorted_channels)

        channel_epg_mappings = []
        name_counts = {}
        for tv_channel in sorted_channels:
            if not tv_channel.epg_id:
                continue
            epg_channel = epg_lookup.get((tv_channel.epg_source_id, tv_channel.epg_id))
            if epg_channel is None:
                continue
            base_name = tv_channel.name
            if base_name in name_counts:
                name_counts[base_name] += 1
                display_name = f"{base_name} {name_counts[base_name]}"
                epg_id = f"{tv_channel.epg_id}.{name_counts[base_name]}"
            else:
                name_counts[base_name] = 1
                display_name = base_name
                epg_id = tv_channel.epg_id
            channel_epg_mappings.append({'epg_id': epg_id, 'display_name': display_name, 'tv_channel': tv_channel, 'epg_channel': epg_channel})

        for mapping in channel_epg_mappings:
            xml_lines.append(f'  <channel id="{html.escape(mapping["epg_id"])}">')
            xml_lines.append(f'    <display-name>{html.escape(mapping["display_name"])}</display-name>')
            if mapping['tv_channel'].logo_url:
                xml_lines.append(f'    <icon src="{html.escape(mapping["tv_channel"].logo_url)}" />')
            xml_lines.append('  </channel>')
        xml_lines.append('')

        programs_by_channel = self.programs_in_window([m['epg_channel'].id for m in channel_epg_mappings], days_back, days_forward)
        for mapping in channel_epg_mappings:
            for program in programs_by_channel.get(mapping['epg_channel'].id, []):
                xml_lines.extend(self.programme_xml_lines(program, mapping['epg_id']))
        xml_lines.append('</tv>')
        return '\n'.join(xml_lines)

    def epg_channel_lookup(self, tv_channels: List[TVChannel]) -> Dict[Tuple[Optional[int], str], EPGChannel]:
        source_ids = {c.epg_source_id for c in tv_channels if c.epg_source_id is not None}
        xml_ids = {c.epg_id for c in tv_channels if c.epg_id}
        if not source_ids or not xml_ids:
            return {}
        rows = self.db.query(EPGChannel).filter(EPGChannel.epg_source_id.in_(source_ids), EPGChannel.channel_xml_id.in_(xml_ids)).all()
        return {(row.epg_source_id, row.channel_xml_id): row for row in rows}

    def programs_in_window(self, epg_channel_ids: List[int], days_back: int = 1, days_forward: int = 7) -> Dict[int, List[EPGProgram]]:
        if not epg_channel_ids:
            return {}
        now = datetime.now(timezone.utc)
        rows = (
            self.db.query(EPGProgram)
            .filter(EPGProgram.epg_channel_id.in_(epg_channel_ids),
                    EPGProgram.start_time >= now - timedelta(days=days_back),
                    EPGProgram.end_time <= now + timedelta(days=days_forward))
            .order_by(EPGProgram.epg_channel_id, EPGProgram.start_time)
            .all()
        )
        grouped: Dict[int, List[EPGProgram]] = {}
        for program in rows:
            grouped.setdefault(program.epg_channel_id, []).append(program)
        return grouped

    @staticmethod
    def programme_xml_lines(program: EPGProgram, channel_id: str) -> List[str]:
        start = program.start_time.strftime("%Y%m%d%H%M%S %z")
        stop = program.end_time.strftime("%Y%m%d%H%M%S %z")
        if '+' not in start and '-' not in start:
            start += ' +0000'
        if '+' not in stop and '-' not in stop:
            stop += ' +0000'
        lines = [f'  <programme start="{start}" stop="{stop}" channel="{html.escape(channel_id)}">',
                 f'    <title>{html.escape(program.title)}</title>']
        if program.subtitle:
            lines.append(f'    <sub-title>{html.escape(program.subtitle)}</sub-title>')
        if program.description:
            lines.append(f'    <desc>{html.escape(program.description)}</desc>')
        if program.category:
            lines.append(f'    <category>{html.escape(program.category)}</category>')
        if program.image_url:
            lines.append(f'    <icon src="{html.escape(program.image_url)}" />')
        lines.append('  </programme>')
        return lines
```

Keep the original per-line formatting exactly (indentation, `<icon src="..." />`, blank line after the channels) so `test_epg_xml_output_unchanged_by_refactor` and `parity/test_output_parity.py` pass.

- [ ] **Step 4: Tuner builders**

Append to `TunerService`:

```python
    def build_guide_xml(self, lineup: Lineup, days_back: int = 1, days_forward: int = 7) -> str:
        """XMLTV whose channel ids are the lineup's GuideNumbers (Plex/Jellyfin HDHR matching)."""
        import html
        from app.services.epg_service import EPGService

        epg = EPGService(self.db)
        tv_by_id = {tv.id: tv for tv in self.db.query(TVChannel).filter(TVChannel.id.in_([e.tv_channel_id for e in lineup.entries])).all()} if lineup.entries else {}
        lookup = epg.epg_channel_lookup(list(tv_by_id.values()))
        lines = [
            '<?xml version="1.0" encoding="utf-8" ?>',
            '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
            '<tv generator-info-name="Acestream Scraper Tuner Guide" generator-info-url="https://github.com/pipepito/acestream-scraper">',
        ]
        mapped = []
        for entry in lineup.entries:
            lines.append(f'  <channel id="{entry.guide_number}">')
            lines.append(f'    <display-name>{entry.guide_number} {html.escape(entry.guide_name)}</display-name>')
            lines.append(f'    <display-name>{entry.guide_number}</display-name>')
            lines.append(f'    <display-name>{html.escape(entry.guide_name)}</display-name>')
            if entry.logo_url:
                lines.append(f'    <icon src="{html.escape(entry.logo_url)}" />')
            lines.append('  </channel>')
            epg_channel = lookup.get((entry.epg_source_id, entry.epg_id)) if entry.epg_id else None
            if epg_channel is not None:
                mapped.append((entry, epg_channel))
        lines.append('')
        programs = epg.programs_in_window([c.id for _, c in mapped], days_back, days_forward)
        for entry, epg_channel in mapped:
            for program in programs.get(epg_channel.id, []):
                lines.extend(epg.programme_xml_lines(program, entry.guide_number))
        lines.append('</tv>')
        return '\n'.join(lines)

    @staticmethod
    def build_playlist_m3u(lineup: Lineup, public_base_url: str) -> str:
        """M3U for Jellyfin's M3U tuner: tvg-id keeps the upstream EPG id, stream URLs are the relay."""
        from app.services.playlist_service import PlaylistService

        base = public_base_url.rstrip('/')
        lines = ["#EXTM3U"]
        for entry in lineup.entries:
            attrs = []
            if entry.epg_id:
                attrs.append(f'tvg-id="{PlaylistService._attr(entry.epg_id)}"')
            attrs.append(f'tvg-chno="{entry.guide_number}"')
            attrs.append(f'tvg-name="{PlaylistService._attr(entry.guide_name)}"')
            if entry.logo_url:
                attrs.append(f'tvg-logo="{PlaylistService._attr(entry.logo_url)}"')
            if entry.category:
                attrs.append(f'group-title="{PlaylistService._attr(entry.category)}"')
            lines.append(f'#EXTINF:-1 {" ".join(attrs)},{PlaylistService._attr(entry.guide_name)}')
            lines.append(f"{base}/tuner/stream/{entry.content_id}.ts")
        return "\n".join(lines) + "\n"
```

- [ ] **Step 5: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_exports.py backend/tests/test_epg.py backend/tests/parity backend/tests/regression backend/tests/test_legacy_playlist_routes.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/epg_service.py backend/app/services/tuner_service.py backend/tests/test_tuner_exports.py backend/tests/test_epg.py
git commit -m "feat(tuner): numeric-id guide and relay playlist on a refactored EPG export"
```

---

### Task 3: Tuner routes and the token-gated settings/status API

**Files:**
- Modify: `backend/app/api/endpoints/tuner.py`, `backend/app/api/api.py`, `backend/app/services/tuner_network.py` (concurrency cap), `backend/app/api/endpoints/tuner.py`
- Create: `backend/app/schemas/tuner.py`
- Test: `backend/tests/test_tuner_routes.py`, `backend/tests/test_api_token_auth.py`

**Interfaces:**
- Produces on `hdhr_router`: `GET /tuner/discover.json`, `GET /tuner/lineup.json`, `GET /tuner/lineup_status.json`, `POST /tuner/lineup.post`, `GET /tuner/device.xml`, `GET /tuner/guide.xml`, `GET /tuner/playlist.m3u`, `GET /tuner/epg.xml`; `/tuner/stream/{id}.ts` capped at `tuner_count` concurrent relays (503 `TUNER_BUSY`).
- On `router` (`/api/v1/tuner`): `GET/PUT /settings` (`TunerSettingsResponse`/`TunerSettingsUpdate`), `GET /status` (`TunerStatusResponse{channel_count, renumbered, overflow, device_id, urls{tuner, lineup, guide, playlist, epg, stream_template}, ffmpeg_available, allowed_networks, client_ip, peer, client_allowed, client_source, warnings, recent_denials}`).

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_tuner_routes.py`:

```python
import json

import pytest

from app.config.settings import get_settings
from app.services.tuner_network import get_tuner_gate

IH = "a" * 40


@pytest.fixture
def open_gate(monkeypatch):
    monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    yield
    get_settings.cache_clear(); get_tuner_gate.cache_clear()


def _seed(db):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name="DAZN 1", channel_number=12, epg_id="DAZN LaLiga HD", category="Sports", is_active=True, logo_url="http://logo")
    db.add(tv); db.flush()
    db.add(AcestreamChannel(id=IH, name="feed", is_online=True, is_active=True, tv_channel_id=tv.id)); db.commit()
    return tv


def test_discover_lineup_status_and_device_xml(client, db_session, open_gate):
    _seed(db_session)
    discover = client.get("/tuner/discover.json", headers={"Host": "scraper.lan:8000"}).json()
    assert discover["Manufacturer"] == "Silicondust" and discover["ModelNumber"] == "HDTC-2US"
    assert discover["FirmwareName"] == "hdhomeruntc_atsc" and discover["FirmwareVersion"] == "20240101"
    assert discover["BaseURL"] == "http://scraper.lan:8000/tuner" and discover["LineupURL"] == "http://scraper.lan:8000/tuner/lineup.json"
    assert discover["TunerCount"] == 4 and discover["DeviceAuth"] == "" and len(discover["DeviceID"]) == 8
    lineup = client.get("/tuner/lineup.json", headers={"Host": "scraper.lan:8000"}).json()
    assert lineup == [{"GuideNumber": "12", "GuideName": "DAZN 1", "URL": f"http://scraper.lan:8000/tuner/stream/{IH}.ts"}]
    assert client.get("/tuner/lineup_status.json").json() == {"ScanInProgress": 0, "ScanPossible": 0, "Source": "Cable", "SourceList": ["Cable"]}
    assert client.post("/tuner/lineup.post").status_code == 200
    xml = client.get("/tuner/device.xml", headers={"Host": "scraper.lan:8000"})
    assert xml.headers["content-type"].startswith("application/xml")
    assert f"uuid:{discover['DeviceID']}" in xml.text and "<URLBase>http://scraper.lan:8000/tuner</URLBase>" in xml.text


def test_guide_playlist_and_epg_variants(client, db_session, open_gate):
    _seed(db_session)
    guide = client.get("/tuner/guide.xml")
    assert guide.status_code == 200 and '<channel id="12">' in guide.text and "content-encoding" not in guide.headers
    playlist = client.get("/tuner/playlist.m3u", headers={"Host": "scraper.lan:8000"}).text
    assert 'tvg-id="DAZN LaLiga HD"' in playlist and f"http://scraper.lan:8000/tuner/stream/{IH}.ts" in playlist
    epg = client.get("/tuner/epg.xml")
    assert epg.status_code == 200 and epg.headers["content-type"].startswith("application/xml")


def test_settings_and_status_are_token_gated_and_reflect_the_gate(client, db_session, open_gate, monkeypatch):
    _seed(db_session)
    body = client.get("/api/v1/tuner/status").json()
    assert body["channel_count"] == 1 and body["renumbered"] == [] and body["overflow"] == 0
    assert body["urls"]["lineup"].endswith("/tuner/lineup.json") and body["urls"]["stream_template"].endswith("/tuner/stream/{content_id}.ts")
    assert body["client_allowed"] is True and body["client_source"] == "direct" and body["allowed_networks"] == ["*"]
    assert isinstance(body["ffmpeg_available"], bool)
    updated = client.put("/api/v1/tuner/settings", json={"friendly_name": "Lounge", "tuner_count": 2, "max_channels": 100, "only_online": True}).json()
    assert updated == {"friendly_name": "Lounge", "tuner_count": 2, "max_channels": 100, "only_online": True}
    assert client.get("/tuner/discover.json").json()["FriendlyName"] == "Lounge"
    assert client.put("/api/v1/tuner/settings", json={"max_channels": 0}).status_code == 422

    monkeypatch.setenv("API_TOKEN", "t")
    assert client.get("/api/v1/tuner/status").status_code == 401
    assert client.get("/tuner/discover.json").status_code == 200


def test_status_reports_docker_gateway_warning_and_denials(client, db_session, monkeypatch):
    monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "10.0.0.0/8")
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    try:
        assert client.get("/tuner/lineup.json").status_code == 403
        body = client.get("/api/v1/tuner/status").json()
        assert body["client_allowed"] is False
        assert body["recent_denials"][0]["path"] == "/tuner/lineup.json"
        gate = get_tuner_gate()
        assert gate.classify_source("172.17.0.1", False) == "docker-gateway"
    finally:
        get_settings.cache_clear(); get_tuner_gate.cache_clear()


def test_stream_relays_are_capped_by_tuner_count(client, db_session, open_gate, monkeypatch):
    import app.api.endpoints.tuner as tuner_module
    from app.services.stream_relay import relay_registry
    from app.services.tuner_service import TunerService
    TunerService(db_session).update_settings(tuner_count=1)
    relay_registry.open(IH, "tuner:test")  # one active relay already
    try:
        response = client.get(f"/tuner/stream/{IH}.ts")
        assert response.status_code == 503 and response.json()["error"]["code"] == "TUNER_BUSY"
    finally:
        for info in relay_registry.active():
            relay_registry.close(info.id)
```

Append to `backend/tests/test_api_token_auth.py` `TestTokenEnforced`:

```python
    def test_tuner_admin_routes_require_token_but_tuner_routes_stay_public(self, client, token_enabled, monkeypatch):
        from app.config.settings import get_settings
        from app.services.tuner_network import get_tuner_gate
        monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
        get_settings.cache_clear(); get_tuner_gate.cache_clear()
        try:
            assert client.get("/api/v1/tuner/settings").status_code == 401
            assert client.get("/api/v1/tuner/status").status_code == 401
            assert client.get("/tuner/discover.json").status_code == 200
            assert client.get("/tuner/settings").status_code == 404
        finally:
            get_settings.cache_clear(); get_tuner_gate.cache_clear()
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_routes.py`
Expected: FAIL (404/HTML).

- [ ] **Step 3: Schemas**

Create `backend/app/schemas/tuner.py`:

```python
"""DTOs for /api/v1/tuner (spec 7.2)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TunerSettingsResponse(BaseModel):
    friendly_name: str
    tuner_count: int
    max_channels: int
    only_online: bool


class TunerSettingsUpdate(BaseModel):
    friendly_name: Optional[str] = Field(None, max_length=255)
    tuner_count: Optional[int] = Field(None, ge=1, le=16)
    max_channels: Optional[int] = Field(None, ge=1, le=1000)
    only_online: Optional[bool] = None


class TunerRenumbered(BaseModel):
    tv_channel_id: int
    name: str
    requested_number: int
    assigned_number: int


class TunerUrls(BaseModel):
    tuner: str
    lineup: str
    guide: str
    playlist: str
    epg: str
    stream_template: str


class TunerDenial(BaseModel):
    client_ip: str
    peer: str
    path: str
    at: float


class TunerStatusResponse(BaseModel):
    channel_count: int
    renumbered: List[TunerRenumbered]
    overflow: int
    device_id: str
    urls: TunerUrls
    ffmpeg_available: bool
    allowed_networks: List[str]
    client_ip: Optional[str] = None
    peer: Optional[str] = None
    client_allowed: bool
    client_source: Literal["direct", "forwarded", "docker-gateway", "loopback"]
    warnings: List[str]
    recent_denials: List[TunerDenial]
```

- [ ] **Step 4: Routes**

In `backend/app/api/endpoints/tuner.py` add (above the catch-all, keeping `tuner_stream` where it is) imports for `TunerService`, `resolve_public_base_url`, `get_tuner_gate`, `relay_registry`, `player_service`, the DTOs, `JSONResponse`, `PlainTextResponse`; a helper:

```python
def _public(request: Request, db: Session) -> str:
    return resolve_public_base_url(request, SettingsRepository(db)).url


def _discover(request: Request, db: Session) -> dict:
    service = TunerService(db)
    settings = service.settings()
    public = _public(request, db)
    return {
        "FriendlyName": settings.friendly_name, "Manufacturer": "Silicondust", "ModelNumber": "HDTC-2US",
        "FirmwareName": "hdhomeruntc_atsc", "FirmwareVersion": "20240101", "DeviceID": service.device_id(), "DeviceAuth": "",
        "BaseURL": f"{public}/tuner", "LineupURL": f"{public}/tuner/lineup.json", "TunerCount": settings.tuner_count,
    }
```

and the routes:

```python
@hdhr_router.get("/discover.json", include_in_schema=False)
def discover(request: Request, db: Session = Depends(get_db)):
    return JSONResponse(_discover(request, db), headers={"Cache-Control": "no-store"})


@hdhr_router.get("/lineup.json", include_in_schema=False)
def lineup(request: Request, db: Session = Depends(get_db)):
    public = _public(request, db)
    entries = TunerService(db).build_lineup().entries
    return JSONResponse([{"GuideNumber": e.guide_number, "GuideName": e.guide_name, "URL": f"{public}/tuner/stream/{e.content_id}.ts"} for e in entries],
                        headers={"Cache-Control": "no-store"})


@hdhr_router.get("/lineup_status.json", include_in_schema=False)
def lineup_status():
    return {"ScanInProgress": 0, "ScanPossible": 0, "Source": "Cable", "SourceList": ["Cable"]}


@hdhr_router.api_route("/lineup.post", methods=["GET", "POST"], include_in_schema=False)
def lineup_post():
    return Response(status_code=200)


@hdhr_router.get("/device.xml", include_in_schema=False)
def device_xml(request: Request, db: Session = Depends(get_db)):
    info = _discover(request, db)
    body = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<root xmlns="urn:schemas-upnp-org:device-1-0">\n'
        '  <specVersion><major>1</major><minor>0</minor></specVersion>\n'
        f'  <URLBase>{info["BaseURL"]}</URLBase>\n'
        '  <device>\n'
        '    <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>\n'
        f'    <friendlyName>{html.escape(info["FriendlyName"])}</friendlyName>\n'
        '    <manufacturer>Silicondust</manufacturer>\n'
        '    <modelName>HDTC-2US</modelName>\n'
        '    <modelNumber>HDTC-2US</modelNumber>\n'
        f'    <serialNumber>{info["DeviceID"]}</serialNumber>\n'
        f'    <UDN>uuid:{info["DeviceID"]}</UDN>\n'
        '  </device>\n'
        '</root>\n'
    )
    return Response(content=body, media_type="application/xml")


@hdhr_router.get("/guide.xml", include_in_schema=False)
def guide_xml(db: Session = Depends(get_db)):
    service = TunerService(db)
    return Response(content=service.build_guide_xml(service.build_lineup()), media_type="application/xml", headers={"Cache-Control": "no-store"})


@hdhr_router.get("/playlist.m3u", include_in_schema=False)
def playlist_m3u(request: Request, db: Session = Depends(get_db)):
    service = TunerService(db)
    return PlainTextResponse(service.build_playlist_m3u(service.build_lineup(), _public(request, db)), headers={"Cache-Control": "no-store"})


@hdhr_router.get("/epg.xml", include_in_schema=False)
def epg_xml(db: Session = Depends(get_db)):
    from app.services.epg_service import EPGService
    ids = [e.tv_channel_id for e in TunerService(db).build_lineup().entries]
    return Response(content=EPGService(db).generate_epg_xml(tv_channel_ids=ids), media_type="application/xml", headers={"Cache-Control": "no-store"})
```

In `tuner_stream`, before starting the relay (after the HEAD early return) add the cap:

```python
    limit = TunerService(db).settings().tuner_count
    if relay_registry.count_active() >= limit:
        raise APIError(code="TUNER_BUSY", message=f"All {limit} tuner slots are in use", status_code=503, context={"limit": limit})
```

Token-gated `router`:

```python
@router.get("/settings", response_model=TunerSettingsResponse)
def get_tuner_settings(db: Session = Depends(get_db)):
    return TunerService(db).settings().__dict__


@router.put("/settings", response_model=TunerSettingsResponse)
def update_tuner_settings(payload: TunerSettingsUpdate, db: Session = Depends(get_db)):
    return TunerService(db).update_settings(**payload.model_dump(exclude_none=True)).__dict__


@router.get("/status", response_model=TunerStatusResponse)
def tuner_status(request: Request, db: Session = Depends(get_db)):
    service = TunerService(db)
    lineup = service.build_lineup()
    public = _public(request, db)
    gate = get_tuner_gate()
    peer = (getattr(request.state, "peer", None) or (None, 0))[0]
    client_ip = request.client.host if request.client else None
    forwarded = bool(getattr(request.state, "forwarded", False))
    source = gate.classify_source(peer, forwarded)
    warnings = []
    if source in ("docker-gateway", "loopback") and not forwarded:
        warnings.append("TUNER_ALLOWLIST_INEFFECTIVE")
    if lineup.overflow:
        warnings.append("TUNER_LINEUP_CAPPED")
    return TunerStatusResponse(
        channel_count=len(lineup.entries), renumbered=[r.__dict__ for r in lineup.renumbered], overflow=lineup.overflow,
        device_id=service.device_id(),
        urls=TunerUrls(tuner=f"{public}/tuner", lineup=f"{public}/tuner/lineup.json", guide=f"{public}/tuner/guide.xml",
                       playlist=f"{public}/tuner/playlist.m3u", epg=f"{public}/tuner/epg.xml", stream_template=f"{public}/tuner/stream/{{content_id}}.ts"),
        ffmpeg_available=player_service.capabilities()["ffmpeg_available"],
        allowed_networks=gate.allowed_networks, client_ip=client_ip, peer=peer,
        client_allowed=gate.is_allowed(peer) and gate.is_allowed(client_ip), client_source=source, warnings=warnings,
        recent_denials=[d.__dict__ for d in gate.recent_denials()],
    )
```

`api.py`: `api_router.include_router(tuner.router, prefix="/tuner", tags=["tuner"])`.

- [ ] **Step 5: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_routes.py backend/tests/test_tuner_network.py backend/tests/test_api_token_auth.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/endpoints/tuner.py backend/app/api/api.py backend/app/schemas/tuner.py backend/tests/test_tuner_routes.py backend/tests/test_api_token_auth.py
git commit -m "feat(tuner): HDHomeRun discover/lineup/guide routes and the tuner settings/status API"
```

---

### Task 4: Jellyfin and Plex clients, media server service and sync job

**Files:**
- Create: `backend/app/services/media_servers/__init__.py`, `backend/app/services/media_servers/base.py`, `backend/app/services/media_servers/jellyfin.py`, `backend/app/services/media_servers/plex.py`, `backend/app/services/media_servers/service.py`, `backend/app/repositories/media_server_repository.py`, `backend/app/tasks/media_server_sync_task.py`
- Test: `backend/tests/test_media_servers.py`

**Interfaces:**
- Produces: `MediaServerUnreachable`, `MediaServerAuthError`, `MediaServerError(status_code, message)`; `JellyfinClient(base_url, api_key, device_id, app_version, client=None)` with `public_info()`, `livetv_config()`, `save_tuner_host(payload)`, `delete_tuner_host(id)`, `save_listing_provider(payload)`, `delete_listing_provider(id)`, `scheduled_tasks()`, `start_task(id)`, `channel_count()`; `PlexClient(base_url, token, client=None)` with `identity()`, `dvrs()`, `reload_guide(key)`; `MediaServerRepository`; `MediaServerService(db, client_factory=new_client, settings_getter=get_settings)` with `validate_base_url(url)`, `test(kind, base_url, api_key, stored_id)`, `connect(server, public_base_url)`, `refresh(server)` → `RefreshResult(status, message)`, `status(server)`, `disconnect(server)`, `sync_if_changed(server) -> RefreshResult|None`; `run_media_server_sync_task()`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_media_servers.py`:

```python
"""Jellyfin/Plex sync (spec 7.3) against recorded fake servers."""
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.services.media_servers.base import MediaServerAuthError
from app.services.media_servers.service import MediaServerService

PUBLIC = "http://scraper.lan:8000"


class FakeJellyfin:
    """Enough of the Jellyfin API for the client: tuners/providers upsert, tasks, channels."""

    def __init__(self):
        self.tuners = {}
        self.providers = {}
        self.started = []
        self.requests = []
        self.refresh_state = "Idle"
        self.reject_key = False

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        auth = request.headers.get("Authorization", "")
        path = request.url.path
        if path == "/System/Info/Public":
            return httpx.Response(200, json={"Version": "10.11.11", "ServerName": "jf"})
        if not auth.startswith('MediaBrowser Token="good"') or self.reject_key:
            return httpx.Response(401, text="Unauthorized")
        if path == "/System/Configuration/livetv":
            return httpx.Response(200, json={"TunerHosts": list(self.tuners.values()), "ListingProviders": list(self.providers.values()), "GuideDays": 7})
        if path == "/LiveTv/TunerHosts" and request.method == "POST":
            body = json.loads(request.content)
            body["Id"] = body.get("Id") or f"tuner{len(self.tuners) + 1}"
            self.tuners[body["Id"]] = body
            return httpx.Response(200, json=body)
        if path == "/LiveTv/TunerHosts" and request.method == "DELETE":
            self.tuners.pop(request.url.params["id"], None)
            return httpx.Response(204)
        if path == "/LiveTv/ListingProviders" and request.method == "POST":
            body = json.loads(request.content)
            body["Id"] = body.get("Id") or f"prov{len(self.providers) + 1}"
            self.providers[body["Id"]] = body
            return httpx.Response(200, json=body)
        if path == "/LiveTv/ListingProviders" and request.method == "DELETE":
            self.providers.pop(request.url.params["id"], None)
            return httpx.Response(204)
        if path == "/ScheduledTasks":
            return httpx.Response(200, json=[{"Id": "abc", "Key": "RefreshGuide", "Name": "Refresh Guide", "State": self.refresh_state, "LastExecutionResult": {"Status": "Completed"}}, {"Id": "x", "Key": "Other", "State": "Idle"}])
        if path == "/ScheduledTasks/Running/abc" and request.method == "POST":
            self.started.append(1)
            return httpx.Response(204)
        if path == "/LiveTv/Channels":
            return httpx.Response(200, json={"Items": [], "TotalRecordCount": 42})
        return httpx.Response(404)


@pytest.fixture
def jellyfin():
    return FakeJellyfin()


def _service(db, handler):
    return MediaServerService(db, client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)))


def _server(svc, **overrides):
    fields = dict(kind="jellyfin", name="Jelly", base_url="http://jellyfin.lan:8096", api_key="good", tuner_mode="hdhomerun")
    fields.update(overrides)
    return svc.repo.create(**fields)


def test_validate_base_url(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    assert svc.validate_base_url(" http://jellyfin.lan:8096/ ") == "http://jellyfin.lan:8096"
    assert svc.validate_base_url("https://plex.lan:32400/plex") == "https://plex.lan:32400/plex"
    for bad in ("jellyfin.lan", "http://user:pw@host", "http://169.254.169.254:8096", "ftp://x"):
        with pytest.raises(Exception):
            svc.validate_base_url(bad)


def test_jellyfin_connect_upserts_and_refresh_triggers_task(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc)
    svc.connect(server, PUBLIC)
    assert server.tuner_host_id == "tuner1" and server.listing_provider_id == "prov1" and server.server_version == "10.11.11"
    tuner = jellyfin.tuners["tuner1"]
    assert tuner["Type"] == "hdhomerun" and tuner["Url"] == f"{PUBLIC}/tuner" and tuner["AllowHWTranscoding"] is False and tuner["TunerCount"] == 0
    provider = jellyfin.providers["prov1"]
    assert provider["Type"] == "xmltv" and provider["Path"] == f"{PUBLIC}/tuner/guide.xml" and provider["EnabledTuners"] == ["tuner1"] and provider["EnableAllTuners"] is False
    header = next(r.headers["Authorization"] for r in jellyfin.requests if "Authorization" in r.headers)
    assert 'Client="acestream-scraper"' in header and 'DeviceId="' in header and 'Version="' in header
    # Reconnect reuses the ids (no duplicates)
    svc.connect(server, PUBLIC)
    assert len(jellyfin.tuners) == 1 and len(jellyfin.providers) == 1

    result = svc.refresh(server)
    assert result.status == "ok" and jellyfin.started == [1]
    jellyfin.refresh_state = "Running"
    assert svc.refresh(server).status == "ok" and jellyfin.started == [1]  # already running: not re-triggered

    status = svc.status(server)
    assert status["connected"] is True and status["channel_count"] == 42 and status["refresh_state"] == "Running"

    svc.disconnect(server)
    assert jellyfin.tuners == {} and jellyfin.providers == {} and server.tuner_host_id is None


def test_jellyfin_m3u_mode_uses_playlist_and_epg(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc, tuner_mode="m3u")
    svc.connect(server, PUBLIC)
    assert jellyfin.tuners["tuner1"]["Type"] == "m3u" and jellyfin.tuners["tuner1"]["Url"] == f"{PUBLIC}/tuner/playlist.m3u"
    assert jellyfin.providers["prov1"]["Path"] == f"{PUBLIC}/tuner/epg.xml"


def test_test_uses_stored_key_when_none_given_and_maps_auth(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc)
    probe = svc.test("jellyfin", "http://jellyfin.lan:8096", None, stored_id=server.id)
    assert probe["reachable"] and probe["authenticated"] and probe["version"] == "10.11.11"
    probe = svc.test("jellyfin", "http://jellyfin.lan:8096", "bad", stored_id=None)
    assert probe["reachable"] and probe["authenticated"] is False
    jellyfin.reject_key = True
    with pytest.raises(MediaServerAuthError):
        svc.refresh(server)


class FakePlex:
    def __init__(self):
        self.reloads = []

    def handler(self, request):
        path = request.url.path
        if path == "/identity":
            return httpx.Response(200, json={"MediaContainer": {"version": "1.43.0.1", "machineIdentifier": "m"}})
        if request.headers.get("X-Plex-Token") != "tok":
            return httpx.Response(401)
        if path == "/livetv/dvrs":
            return httpx.Response(200, json={"MediaContainer": {"Dvr": [{"key": "7", "uuid": "u", "lineup": "lineup://tv.plex.providers.epg.xmltv/x", "Device": [{"uri": f"device://tv.plex.grabbers.hdhomerun/{'A' * 8}", "uuid": "d"}]}]}})
        if path == "/livetv/dvrs/7/reloadGuide" and request.method == "POST":
            self.reloads.append(1)
            return httpx.Response(200)
        return httpx.Response(404)


def test_plex_connect_finds_the_dvr_and_refreshes(alembic_db_session, monkeypatch):
    plex = FakePlex()
    svc = _service(alembic_db_session, plex.handler)
    server = svc.repo.create(kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key="tok", tuner_mode="hdhomerun")
    monkeypatch.setattr("app.services.media_servers.service.TunerService.device_id", lambda self: "A" * 8)
    svc.connect(server, PUBLIC)
    assert server.dvr_key == "7"
    assert svc.refresh(server).status == "ok" and plex.reloads == [1]
    instructions = svc.status(server)
    assert instructions["steps"] and f"{PUBLIC}/tuner/guide.xml" in json.dumps(instructions)


def test_plex_without_token_is_manual(alembic_db_session):
    plex = FakePlex()
    svc = _service(alembic_db_session, plex.handler)
    server = svc.repo.create(kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key=None, tuner_mode="hdhomerun")
    assert svc.refresh(server).status == "manual"


def test_sync_if_changed_debounces_and_records_manual(alembic_db_session, jellyfin, monkeypatch):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc)
    svc.connect(server, PUBLIC)
    monkeypatch.setenv("MEDIA_SERVER_MIN_REFRESH_MINUTES", "30")
    from app.config.settings import get_settings
    get_settings.cache_clear()
    try:
        first = svc.sync_if_changed(server)
        assert first is not None and first.status == "ok" and jellyfin.started == [1]
        assert svc.sync_if_changed(server) is None  # nothing changed
        # Lineup changes but the debounce window has not elapsed
        from app.models.models import AcestreamChannel, TVChannel
        tv = TVChannel(name="New", channel_number=3, is_active=True); alembic_db_session.add(tv); alembic_db_session.flush()
        alembic_db_session.add(AcestreamChannel(id="b" * 40, name="f", is_online=True, is_active=True, tv_channel_id=tv.id)); alembic_db_session.commit()
        assert svc.sync_if_changed(server) is None and jellyfin.started == [1]
        server.last_sync_at = datetime.now(timezone.utc) - timedelta(minutes=31); alembic_db_session.commit()
        assert svc.sync_if_changed(server).status == "ok" and jellyfin.started == [1, 1]
        # Plex without token: manual status stored, last_sync_at untouched
        plex = svc.repo.create(kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key=None, tuner_mode="hdhomerun")
        assert svc.sync_if_changed(plex).status == "manual"
        assert plex.last_sync_status == "manual" and plex.last_sync_at is None and plex.last_lineup_fingerprint
    finally:
        get_settings.cache_clear()
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_media_servers.py`
Expected: FAIL.

- [ ] **Step 3: Base, clients, repository**

`backend/app/services/media_servers/__init__.py`: empty.

`backend/app/services/media_servers/base.py`:

```python
"""Shared errors/client for Jellyfin and Plex adapters (spec 7.3)."""
from __future__ import annotations

from typing import Optional

import httpx

from app.utils.url_guard import BlockedURLError, validate_lan_target

CLIENT_TIMEOUT = httpx.Timeout(10.0, connect=3.0)


class MediaServerUnreachable(RuntimeError):
    pass


class MediaServerAuthError(RuntimeError):
    pass


class MediaServerError(RuntimeError):
    def __init__(self, status_code: Optional[int], message: str):
        super().__init__(message)
        self.status_code = status_code


def new_client() -> httpx.Client:
    return httpx.Client(follow_redirects=False, timeout=CLIENT_TIMEOUT)


def guard(host: str) -> None:
    try:
        validate_lan_target(host, resolve=True)
    except BlockedURLError as exc:
        raise MediaServerUnreachable(str(exc)) from exc


def raise_for(response: httpx.Response, what: str) -> None:
    if response.status_code in (401, 403):
        raise MediaServerAuthError(f"{what}: the server rejected the API key/token (HTTP {response.status_code})")
    if response.status_code >= 400:
        raise MediaServerError(response.status_code, f"{what}: HTTP {response.status_code} {response.text[:200]}")
```

`backend/app/services/media_servers/jellyfin.py`:

```python
"""Jellyfin 10.9+ Live TV configuration client."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import httpx

from .base import MediaServerUnreachable, guard, new_client, raise_for


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

    def public_info(self) -> dict:
        return self._request("GET", "/System/Info/Public", auth=False).json()

    def livetv_config(self) -> dict:
        return self._request("GET", "/System/Configuration/livetv").json()

    def save_tuner_host(self, payload: dict) -> dict:
        return self._request("POST", "/LiveTv/TunerHosts", json=payload).json()

    def delete_tuner_host(self, tuner_id: str) -> None:
        self._request("DELETE", "/LiveTv/TunerHosts", params={"id": tuner_id})

    def save_listing_provider(self, payload: dict) -> dict:
        return self._request("POST", "/LiveTv/ListingProviders", params={"validateListings": "false", "validateLogin": "false"}, json=payload).json()

    def delete_listing_provider(self, provider_id: str) -> None:
        self._request("DELETE", "/LiveTv/ListingProviders", params={"id": provider_id})

    def scheduled_tasks(self) -> List[dict]:
        return self._request("GET", "/ScheduledTasks").json()

    def start_task(self, task_id: str) -> None:
        self._request("POST", f"/ScheduledTasks/Running/{task_id}")

    def channel_count(self) -> int:
        body = self._request("GET", "/LiveTv/Channels", params={"addCurrentProgram": "false", "enableImages": "false", "limit": "1"}).json()
        return int(body.get("TotalRecordCount") or 0)
```

`backend/app/services/media_servers/plex.py`:

```python
"""Plex Media Server: identity, DVR lookup and guide reload (undocumented owner-token API)."""
from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlsplit

import httpx

from .base import MediaServerUnreachable, guard, new_client, raise_for


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

    def identity(self) -> dict:
        return (self._request("GET", "/identity", auth=False).json() or {}).get("MediaContainer", {})

    def dvrs(self) -> List[dict]:
        return ((self._request("GET", "/livetv/dvrs").json() or {}).get("MediaContainer", {}) or {}).get("Dvr", []) or []

    def find_dvr_key(self, device_id: str) -> Optional[str]:
        needle = f"tv.plex.grabbers.hdhomerun/{device_id}".lower()
        for dvr in self.dvrs():
            for device in dvr.get("Device", []) or []:
                if needle in str(device.get("uri", "")).lower():
                    return str(dvr.get("key"))
        return None

    def reload_guide(self, dvr_key: str) -> None:
        self._request("POST", f"/livetv/dvrs/{dvr_key}/reloadGuide")
```

`backend/app/repositories/media_server_repository.py`:

```python
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import MediaServer


class MediaServerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[MediaServer]:
        return self.db.query(MediaServer).order_by(MediaServer.name).all()

    def get(self, server_id: int) -> Optional[MediaServer]:
        return self.db.query(MediaServer).filter(MediaServer.id == server_id).first()

    def get_by_name(self, name: str) -> Optional[MediaServer]:
        return self.db.query(MediaServer).filter(MediaServer.name == name).first()

    def create(self, *, kind: str, name: str, base_url: str, api_key: Optional[str], tuner_mode: str = "hdhomerun",
               enabled: bool = True, auto_refresh: bool = True) -> MediaServer:
        entry = MediaServer(kind=kind, name=name, base_url=base_url, api_key=api_key, tuner_mode=tuner_mode, enabled=enabled, auto_refresh=auto_refresh)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def save(self, entry: MediaServer) -> MediaServer:
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: MediaServer) -> None:
        self.db.delete(entry)
        self.db.commit()
```

- [ ] **Step 4: Service and task**

`backend/app/services/media_servers/service.py`:

```python
"""Jellyfin/Plex registration, refresh and fingerprint-driven sync (spec 7.3)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from urllib.parse import urlsplit

import httpx
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.models import MediaServer
from app.repositories.media_server_repository import MediaServerRepository
from app.services.tuner_service import TunerService
from app.utils.url_guard import validate_lan_target

from .base import MediaServerAuthError, MediaServerError, MediaServerUnreachable, new_client
from .jellyfin import JellyfinClient
from .plex import PlexClient

APP_VERSION = "2.0.0"

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
            saved_tuner = client.save_tuner_host(tuner_payload)
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
            task = next((t for t in client.scheduled_tasks() if t.get("Key") == "RefreshGuide"), None)
            if task is None:
                return RefreshResult("error", "Jellyfin has no Refresh Guide task (is Live TV set up?)")
            if str(task.get("State", "")).lower() != "running":
                client.start_task(str(task["Id"]))
            return RefreshResult("ok", "Jellyfin is refreshing its guide")
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

    def status(self, server: MediaServer) -> dict:
        public = (self._settings().PUBLIC_BASE_URL or "").rstrip("/")
        tuner = TunerService(self.db)
        base = {"connected": False, "channel_count": None, "refresh_state": None, "last_result": None, "steps": [], "paste": {}}
        if server.kind == "plex":
            base["connected"] = bool(server.dvr_key)
            base["steps"] = PLEX_STEPS
            host_port = urlsplit(public).netloc if public else "<public address>"
            base["paste"] = {"tuner_address": f"{host_port}/tuner", "guide_url": f"{public or '<public address>'}/tuner/guide.xml", "device_id": tuner.device_id()}
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
        server.last_lineup_fingerprint = lineup_fp
        server.last_guide_fingerprint = guide_fp
        server.last_sync_status = result.status
        server.last_error = result.message if result.status == "error" else None
        if result.status == "ok":
            server.last_sync_at = now
        self.repo.save(server)
        return result
```

`backend/app/tasks/media_server_sync_task.py`:

```python
"""Scheduler job: push channel/guide changes to Jellyfin/Plex (spec 7.3)."""
import logging

from app.config.database import SessionLocal
from app.services.media_servers.service import MediaServerService

logger = logging.getLogger(__name__)


def run_media_server_sync_task() -> dict:
    db = SessionLocal()
    try:
        service = MediaServerService(db)
        summary = {"checked": 0, "refreshed": 0, "manual": 0, "errors": 0}
        for server in service.repo.get_all():
            if not server.enabled or not server.auto_refresh:
                continue
            summary["checked"] += 1
            try:
                result = service.sync_if_changed(server)
            except Exception as exc:  # noqa: BLE001 - one server must not stop the others
                logger.exception("Media server sync failed for %s", server.name)
                server.last_sync_status = "error"
                server.last_error = str(exc)
                service.repo.save(server)
                summary["errors"] += 1
                continue
            if result is None:
                continue
            summary["refreshed" if result.status == "ok" else "manual" if result.status == "manual" else "errors"] += 1
        return summary
    finally:
        db.close()
```

- [ ] **Step 5: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_media_servers.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/media_servers backend/app/repositories/media_server_repository.py backend/app/tasks/media_server_sync_task.py backend/tests/test_media_servers.py
git commit -m "feat(media-servers): Jellyfin/Plex clients, sync service and scheduler task"
```

---

### Task 5: Media server endpoints and lifespan job

**Files:**
- Create: `backend/app/schemas/media_servers.py`, `backend/app/api/endpoints/media_servers.py`
- Modify: `backend/app/api/api.py`, `backend/main.py` (register `media_server_sync` every 600 s), `backend/app/utils/format.py`? (no) ; `frontend/src/utils/format.ts` `JOB_NAMES` gets `media_server_sync: 'Sync media servers'`
- Test: `backend/tests/test_media_servers_api.py`

**Interfaces:**
- Produces `/api/v1/media-servers`: `GET ""`, `POST ""` 201, `PATCH /{id}`, `DELETE /{id}` 204 (best-effort disconnect first for a connected Jellyfin), `POST /test` (`MediaServerTestRequest{kind, base_url, api_key?, id?}` → `MediaServerProbeResponse{reachable, authenticated, version, message, tuner_access}`), `POST /{id}/test`, `POST /{id}/connect` → `MediaServerResponse`, `POST /{id}/refresh` → `MediaServerRefreshResponse{status, message, last_sync_at}`, `POST /{id}/disconnect` → `MediaServerResponse`, `GET /{id}/status` → `MediaServerStatusResponse{connected, channel_count, refresh_state, last_result, steps, paste, error}`.
- DTOs: `MediaServerCreate{kind, name, base_url, api_key?, tuner_mode='hdhomerun', enabled=True, auto_refresh=True}`, `MediaServerUpdate` (all optional; `api_key` omitted = keep, "" = clear), `MediaServerResponse{id, kind, name, base_url, tuner_mode, enabled, auto_refresh, has_api_key, connected, tuner_host_id, listing_provider_id, dvr_key, last_sync_at, last_sync_status, last_error, server_version, created_at, updated_at}`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_media_servers_api.py` reusing `FakeJellyfin` from `test_media_servers.py` (import it):

```python
import httpx
import pytest

from tests.test_media_servers import FakeJellyfin, FakePlex


@pytest.fixture
def fakes(monkeypatch):
    import app.api.endpoints.media_servers as endpoint
    jelly, plex = FakeJellyfin(), FakePlex()

    def handler(request):
        return (plex.handler if "plex" in request.url.host else jelly.handler)(request)
    monkeypatch.setattr(endpoint, "_client_factory", lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    return jelly, plex


def _create(client, **overrides):
    body = {"kind": "jellyfin", "name": "Jelly", "base_url": "http://jellyfin.lan:8096", "api_key": "good"}
    body.update(overrides)
    return client.post("/api/v1/media-servers", json=body)


def test_crud_masks_key_and_validates_url(alembic_client, fakes):
    created = _create(alembic_client)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["has_api_key"] is True and "api_key" not in body and body["connected"] is False and body["last_sync_status"] == "never"
    assert _create(alembic_client).status_code == 409
    assert _create(alembic_client, name="bad", base_url="http://169.254.169.254").json()["error"]["code"] == "MEDIA_SERVER_URL_FORBIDDEN"
    patched = alembic_client.patch(f"/api/v1/media-servers/{body['id']}", json={"name": "Jellyfin", "auto_refresh": False})
    assert patched.json()["name"] == "Jellyfin" and patched.json()["auto_refresh"] is False and patched.json()["has_api_key"] is True
    assert alembic_client.delete(f"/api/v1/media-servers/{body['id']}").status_code == 204


def test_connect_refresh_status_disconnect(alembic_client, fakes):
    jelly, _ = fakes
    server = _create(alembic_client).json()
    alembic_client.put("/api/v1/config/public_base_url", json={"value": "http://scraper.lan:8000"})
    connected = alembic_client.post(f"/api/v1/media-servers/{server['id']}/connect")
    assert connected.status_code == 200 and connected.json()["connected"] is True and connected.json()["server_version"] == "10.11.11"
    assert jelly.tuners and jelly.providers
    refreshed = alembic_client.post(f"/api/v1/media-servers/{server['id']}/refresh").json()
    assert refreshed["status"] == "ok" and refreshed["last_sync_at"]
    status = alembic_client.get(f"/api/v1/media-servers/{server['id']}/status").json()
    assert status["connected"] and status["channel_count"] == 42
    jelly.reject_key = True
    failed = alembic_client.post(f"/api/v1/media-servers/{server['id']}/refresh")
    assert failed.status_code == 502 and failed.json()["error"]["code"] == "MEDIA_SERVER_AUTH"
    jelly.reject_key = False
    assert alembic_client.post(f"/api/v1/media-servers/{server['id']}/disconnect").json()["connected"] is False
    assert alembic_client.post(f"/api/v1/media-servers/{server['id']}/refresh").status_code == 200  # refresh works without tuner registration (Jellyfin task)


def test_delete_connected_jellyfin_disconnects_first(alembic_client, fakes):
    jelly, _ = fakes
    server = _create(alembic_client).json()
    alembic_client.post(f"/api/v1/media-servers/{server['id']}/connect")
    assert jelly.tuners
    assert alembic_client.delete(f"/api/v1/media-servers/{server['id']}").status_code == 204
    assert jelly.tuners == {} and jelly.providers == {}


def test_test_endpoint_and_plex_manual(alembic_client, fakes):
    probe = alembic_client.post("/api/v1/media-servers/test", json={"kind": "jellyfin", "base_url": "http://jellyfin.lan:8096", "api_key": "good"}).json()
    assert probe["reachable"] and probe["authenticated"] and probe["version"] == "10.11.11" and "tuner_access" in probe
    plex = _create(alembic_client, kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key=None).json()
    status = alembic_client.get(f"/api/v1/media-servers/{plex['id']}/status").json()
    assert status["steps"] and status["paste"]["guide_url"].endswith("/tuner/guide.xml")
    assert alembic_client.post(f"/api/v1/media-servers/{plex['id']}/refresh").json()["status"] == "manual"


def test_scheduler_registers_the_sync_job():
    import re
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text()
    assert re.search(r'add_interval_task\(run_media_server_sync_task, seconds=600, job_id="media_server_sync"\)', source)
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_media_servers_api.py`
Expected: FAIL.

- [ ] **Step 3: Schemas**

Create `backend/app/schemas/media_servers.py`:

```python
"""DTOs for /api/v1/media-servers (spec 7.3)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MediaServerKind = Literal["jellyfin", "plex"]
TunerMode = Literal["hdhomerun", "m3u"]
SyncStatus = Literal["ok", "error", "never", "manual"]


class MediaServerCreate(BaseModel):
    kind: MediaServerKind
    name: str = Field(..., min_length=1, max_length=255)
    base_url: str = Field(..., min_length=1, max_length=1024)
    api_key: Optional[str] = Field(None, description="Jellyfin API key or Plex owner token")
    tuner_mode: TunerMode = "hdhomerun"
    enabled: bool = True
    auto_refresh: bool = True


class MediaServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[str] = Field(None, min_length=1, max_length=1024)
    api_key: Optional[str] = Field(None, description="omit = keep, empty = clear")
    tuner_mode: Optional[TunerMode] = None
    enabled: Optional[bool] = None
    auto_refresh: Optional[bool] = None


class MediaServerResponse(BaseModel):
    id: int
    kind: MediaServerKind
    name: str
    base_url: str
    tuner_mode: TunerMode
    enabled: bool
    auto_refresh: bool
    has_api_key: bool
    connected: bool
    tuner_host_id: Optional[str] = None
    listing_provider_id: Optional[str] = None
    dvr_key: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: SyncStatus
    last_error: Optional[str] = None
    server_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaServerTestRequest(BaseModel):
    kind: MediaServerKind
    base_url: str
    api_key: Optional[str] = None
    id: Optional[int] = None


class MediaServerProbeResponse(BaseModel):
    reachable: bool
    authenticated: bool
    version: Optional[str] = None
    message: str
    tuner_access: Dict[str, Any]


class MediaServerRefreshResponse(BaseModel):
    status: Literal["ok", "error", "manual"]
    message: Optional[str] = None
    last_sync_at: Optional[datetime] = None


class MediaServerStatusResponse(BaseModel):
    connected: bool
    channel_count: Optional[int] = None
    refresh_state: Optional[str] = None
    last_result: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    paste: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None
```

- [ ] **Step 4: Endpoints and lifespan**

Create `backend/app/api/endpoints/media_servers.py` following `remote_players.py`: `_client_factory = new_client`; `_service(db)`; `_response(server)` computes `connected` as `bool(dvr_key)` for Plex and `bool(tuner_host_id and listing_provider_id)` for Jellyfin and `has_api_key=bool(server.api_key)`; `_translate(exc)` maps `MediaServerAuthError` → 502 `MEDIA_SERVER_AUTH`, `MediaServerUnreachable` → 502 `MEDIA_SERVER_UNREACHABLE`, `MediaServerError` → 502 `MEDIA_SERVER_ERROR` with `context={"status": exc.status_code}`; URL validation errors → 422 `MEDIA_SERVER_URL_FORBIDDEN`; CRUD with 409 on duplicate name; `POST /test` computes `tuner_access` via `RemotePlayerService(db).tuner_access(hostname)` (import from `app.services.remote_players.service`); `POST /{id}/connect` reads the public base URL with `resolve_public_base_url(request, SettingsRepository(db)).url` and calls `service.connect`; `POST /{id}/refresh` calls `service.refresh`, then stores `last_sync_status`/`last_sync_at` (on `ok`) / `last_error` and returns `MediaServerRefreshResponse`; `POST /{id}/disconnect`; `GET /{id}/status` → `MediaServerStatusResponse(**service.status(server))`; `DELETE /{id}` runs `service.disconnect` best-effort (log and continue) when the server is a connected Jellyfin, then deletes. All handlers sync `def`.

`api.py`: `api_router.include_router(media_servers.router, prefix="/media-servers", tags=["media-servers"])`.

`main.py` lifespan: import `run_media_server_sync_task` and add `task_service.add_interval_task(run_media_server_sync_task, seconds=600, job_id="media_server_sync")  # every 10 min` after the channel_status job. `frontend/src/utils/format.ts`: add `media_server_sync: 'Sync media servers'` to `JOB_NAMES` (and the Overview/ScheduledJobs test expectations if they enumerate jobs).

- [ ] **Step 5: Run**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_media_servers_api.py backend/tests/test_background_tasks.py backend/tests/test_error_contracts.py && cd frontend && npm test -- format.test.ts Overview.test.tsx && cd ..`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/media_servers.py backend/app/api/endpoints/media_servers.py backend/app/api/api.py backend/main.py frontend/src/utils/format.ts backend/tests/test_media_servers_api.py
git commit -m "feat(api): media servers CRUD, connect/refresh/status/disconnect and the sync job"
```

---

### Task 6: Frontend — media servers section, tuner diagnostics, page assembly

**Files:**
- Create: `frontend/src/services/mediaServerService.ts`, `frontend/src/services/tunerService.ts`, `frontend/src/hooks/useMediaServers.ts`, `frontend/src/hooks/useTuner.ts`, `frontend/src/components/integrations/MediaServersSection.tsx`, `frontend/src/components/integrations/MediaServerDialog.tsx`
- Modify: `frontend/src/pages/Integrations.tsx`, `frontend/src/components/integrations/PublicAddressSection.tsx` (tuner status alerts)
- Tests: `frontend/src/__tests__/mediaServerService.test.ts`, `frontend/src/__tests__/Integrations.test.tsx`

**Interfaces:**
- Produces `mediaServerService.{list, create, update, remove, test, connect, refresh, disconnect, status}`, `tunerService.{getSettings, updateSettings, getStatus}`; hooks `useMediaServers`, `useCreateMediaServer`, `useUpdateMediaServer`, `useDeleteMediaServer`, `useTestMediaServer`, `useConnectMediaServer`, `useRefreshMediaServer`, `useDisconnectMediaServer`, `useMediaServerStatus(id, enabled)`, `useTunerStatus()`, `useTunerSettings()`, `useUpdateTunerSettings()` (query keys `['media-servers']`, `['tuner','status']`, `['tuner','settings']`).

- [ ] **Step 1: Write the failing tests**

`frontend/src/__tests__/mediaServerService.test.ts` — same shape as `remotePlayerService.test.ts`, asserting paths `/v1/media-servers`, `/v1/media-servers/test`, `/v1/media-servers/1/connect|refresh|disconnect|status`, and `tunerService` paths `/v1/tuner/status`, `/v1/tuner/settings`.

Extend `Integrations.test.tsx`: mock `../hooks/useMediaServers` and `../hooks/useTuner`; the h2 list becomes `['Public address', 'Web player', 'Remote players', 'Media servers']`; add tests:
- a Jellyfin card `role="group" aria-label="Media server Jelly"` shows chips "Connected" and "Guide up to date", two visible buttons `Refresh now Jelly` and `Disconnect Jelly`; the row menu has Edit / Test connection / Delete; clicking Disconnect opens `ConfirmDialog` titled `Disconnect Jelly?` and confirming calls the disconnect mutation; Delete opens `Delete Jelly?`.
- a Plex card without token shows chip "Rescan the guide in Plex", the numbered steps, copy buttons for the tuner address and guide URL, and `Refresh now Plex` disabled; clicking Disconnect on Plex calls the mutation without a dialog.
- the add dialog offers the tuner mode radio only for Jellyfin, and Test connection renders the probe message.
- when `useTunerStatus` returns `warnings: ['TUNER_ALLOWLIST_INEFFECTIVE']` and `recent_denials: [{client_ip: '203.0.113.9', path: '/tuner/lineup.json', at: 1}]`, the Public address section shows both alerts.

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npm test -- mediaServerService.test.ts Integrations.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement**

`mediaServerService.ts` / `tunerService.ts` / hooks mirror plan 3's remote-player files (types from the DTOs above; `useMediaServerStatus` polls every 30 s while enabled; `useTunerStatus` polls every 30 s).

`MediaServerDialog.tsx`: fields kind (Select), name, base URL (helper "Address of Jellyfin/Plex as seen from this server, e.g. http://192.168.1.12:8096"), API key/token (password field; helper per kind: "Jellyfin: Dashboard > API Keys" / "Plex: optional owner token, only needed for automatic guide refresh"), for Jellyfin a `RadioGroup` "Channels reach Jellyfin as" with `hdhomerun` ("HDHomeRun tuner (recommended) — stable channel identity, favorites survive changes") and `m3u` ("M3U playlist + XMLTV — uses tvg-id matching; any change to the address or link format recreates every channel in Jellyfin and drops favorites"), `auto_refresh` switch; "Test connection" via `useTestMediaServer` rendering `message` (+ tuner_access warning: "Jellyfin/Plex at <ip> is outside TUNER_ALLOWED_NETWORKS and will get 403 from the tuner routes; add its network").

`MediaServersSection.tsx`: cards per server with `SYNC_META = { ok: 'Guide up to date', error: 'Refresh failed', never: 'Not synced yet', manual: 'Rescan the guide in Plex' }` chips (warning styling for `manual`/`error`), connection chip, `last_sync_at` via `formatRelativeTime`, channel count from `useMediaServerStatus`; visible actions "Refresh now" (disabled for Plex without token/dvr_key, tooltip "Add a Plex token to refresh automatically") and "Connect"/"Disconnect"; `RowActionsMenu` with Edit, Test connection, Delete (danger); `useConfirm` copy: Disconnect (Jellyfin only) title `Disconnect ${name}?` body "This removes the AceStream tuner and its guide provider from Jellyfin. Jellyfin will re-run Refresh Guide and drop those channels."; Delete title `Delete ${name}?` body for a connected Jellyfin "…also removes the tuner and guide provider from Jellyfin." else "The server is removed from this list."; Plex card body: the numbered `steps` and a paste block with copy buttons (`Copy tuner address`, `Copy guide URL`) plus a Plex Pass note; errors from mutations go through `notify` with `error.code` mapping (`MEDIA_SERVER_AUTH` → "The server rejected the API key/token.", `MEDIA_SERVER_UNREACHABLE` → "The server did not answer. Check the address and that it is reachable from this server.").

`PublicAddressSection.tsx`: consume `useTunerStatus()`; when `warnings` includes `TUNER_ALLOWLIST_INEFFECTIVE` show the Alert "This host hides real client addresses (Docker Desktop, rootless Docker, or IPv6 through docker-proxy); the private-network allowlist cannot tell your LAN from the internet. Publish the port IPv4-only, put a reverse proxy with allow/deny in front, or keep port 8000 off the internet."; when `recent_denials` is non-empty show "Requests from <ip> were denied <relative time> (<path>); add its network to TUNER_ALLOWED_NETWORKS if it is yours." with the newest entry; when `overflow > 0` show "Plex stops saving channel maps at roughly 450-480 channels (it depends on channel number and name length). N channels were left out; disable channels or lower the count." Also add a small "Tuner" form (friendly name, tuner count, max channels, only-online switch) using `useTunerSettings`/`useUpdateTunerSettings` inside this section or a new "Tuner" ContentSection — place it as its own `ContentSection` titled "Tuner" between Web player and Remote players only if the h2 list in the test is updated accordingly; the simplest is a collapsible "Tuner settings" block inside Media servers (keep the h2 list at four).

`Integrations.tsx`: add `<MediaServersSection notify={notify} />` last and a `Media servers` StatusLine item.

- [ ] **Step 4: Run**

Run: `cd frontend && npm test -- mediaServerService.test.ts Integrations.test.tsx && npm run lint -- --max-warnings=0 && npm run typecheck`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/mediaServerService.ts frontend/src/services/tunerService.ts frontend/src/hooks/useMediaServers.ts frontend/src/hooks/useTuner.ts frontend/src/components/integrations frontend/src/pages/Integrations.tsx frontend/src/__tests__/mediaServerService.test.ts frontend/src/__tests__/Integrations.test.tsx
git commit -m "feat(frontend): media servers section, tuner settings and allowlist diagnostics"
```

---

### Task 7: Docs, reverse-proxy guide, contracts, e2e journey and full verification

**Files:**
- Create: `wiki/Media-Servers.md`, `e2e/tests/10-integrations.spec.ts`, `e2e/src/pages/integrations.ts`, `e2e/src/stub-engine.ts`
- Modify: `docs/ops/reverse-proxy.md`, `wiki/Configuration.md`, `wiki/Home.md`, `README.md`, `CLAUDE.md`, `backend/tests/contracts/test_integrations_contracts.py`, `e2e/scenarios/default.json` + `e2e/src/scenario/schema.ts` (optional `integrations` block), `e2e/stack/backend-start.sh` (`FFMPEG_BINARY_PATH` when a host ffmpeg exists)

- [ ] **Step 1: Docs**

`wiki/Media-Servers.md`: requirements (public address reachable from the media server; `/tuner/*` token-free but allowlisted; Docker IPv6/docker-proxy caveat and `0.0.0.0:8000:8000`), Jellyfin (create an API key under Dashboard › API Keys, add the server under Integrations, Connect; HDHomeRun vs M3U modes and the identity caveat; how refresh works: Refresh Guide task, hourly XMLTV cache, 10-minute sync job and `MEDIA_SERVER_MIN_REFRESH_MINUTES`), Plex (Plex Pass; Set Up Plex Tuner › enter address manually › paste `host:port/tuner`; XMLTV guide URL; rescan after channel changes; optional owner token for automatic guide reload; the ~450-480 channel cap and `max_channels`), tuner settings (friendly name, tuner count = concurrent streams, only-online), GuideNumber renumbering note, troubleshooting (403 → allowlist; "device dead" → public address changed; no channels in Jellyfin → check the lineup at `/tuner/lineup.json`).

`docs/ops/reverse-proxy.md`: state that Jellyfin fetches `/tuner/discover.json`, `/tuner/lineup.json`, `/tuner/guide.xml` and the streams with a bare HttpClient and Plex has no credential field, so `/tuner/` cannot sit behind proxy basic auth; add the nginx `location ^~ /tuner/ { auth_basic off; proxy_buffering off; proxy_pass http://127.0.0.1:8000; <same proxy_set_header lines>; }` block before `location /`, the Caddy `handle /tuner/* { reverse_proxy 127.0.0.1:8000 }` before the authed handle, the Traefik `scraper-tuner` router (`PathPrefix(`/tuner/`)`, higher priority, `scraper-gzip` only); note that the proxy must be inside `FORWARDED_ALLOW_IPS` and, when `TUNER_ALLOWED_NETWORKS` is narrowed, inside it too; keep `--no-proxy-headers --timeout-graceful-shutdown 3` in `command:` overrides; verification `curl -s -o /dev/null -w '%{http_code}\n' https://scraper.example.com/tuner/discover.json` (403 from outside the allowlist, 200 from the LAN).

`wiki/Configuration.md`: the media rows from plan 1 plus `MEDIA_SERVER_MIN_REFRESH_MINUTES`; `ALLOW_PRIVATE_SCRAPE_TARGETS` row gains "does not affect remote players, media servers or player discovery, which are LAN targets by design; the metadata/link-local block still applies to them". `wiki/Home.md`: link Web-Player, Remote-Players, Media-Servers. `README.md`: Jellyfin/Plex paragraph.

`docs/ops/acestream-arm-engine.md` (existing, rewritten on `develop` for the 3.2.17 `oci-image` distribution) and the ARM section of `wiki/Docker.md`: add a short "Playing streams on ARM" subsection that states, in plain words, what the media features can promise per platform — amd64 runs the native 3.2.11 engine and is unaffected; arm64 runs the `jopsis/acestream:v3.2.17-fix` distribution whose API and startup are verified but whose live playback is not yet confirmed on hardware, so the web player, remote players and the tuner should work there and any failure surfaces as "The AceStream engine refused to start the stream"; armv7 still runs the official premium-gated 3.1.80 APK, where AceStream's policy (staff posts on forum threads t3928, t3945, t4002) makes live playback outside the Ace Stream app Premium-only, so the media features cannot work without a Premium account. Note that DNS blocklists sinkholing `*.acestream.media` / `*.acestream.net` break the licence path on 3.2.x engines, and that `ACESTREAM_BIND_ALL` reaches every platform through the entrypoint. Do not propose an engine bump or a modified app identity as a fix. Extend `backend/tests/docker/test_docs_contract.py` (or the nearest existing docs contract test under `backend/tests/docker/`) with an assertion that both files contain the phrase "activate premium" and the string `ACESTREAM_BIND_ALL`. `CLAUDE.md`: tuner and media-server domains (routers, services, sync job, settings keys), the `media_server_sync` job in the startup sequence list, and the known limitations (armv7 engine playback is Premium-only; arm64 playback unconfirmed on hardware; Plex cap; plain-text secrets; no seek).

- [ ] **Step 2: Contracts**

Extend `backend/tests/contracts/test_integrations_contracts.py`: exact key sets for `GET /api/v1/tuner/status`, `GET /api/v1/tuner/settings`, `GET /api/v1/media-servers` items, `GET /api/v1/media-servers/{id}/status`, `POST /api/v1/media-servers/test`; `MediaServerCreate` validation (kind/tuner_mode enums); error codes `MEDIA_SERVER_URL_FORBIDDEN`, `TUNER_NETWORK_DENIED`, `TUNER_BUSY`.

- [ ] **Step 3: e2e**

`e2e/src/stub-engine.ts`: a Node `http` server (`startStubEngine(fixturePath): Promise<{ url: string; close: () => Promise<void> }>`) answering `GET /ace/getstream?...&format=json` with `{response: {playback_url: <url>/content/x/1, stat_url: <url>/ace/stat/x/s, command_url: <url>/ace/cmd/x/s, is_live: 1}, error: null}`, `GET /content/x/1` streaming `backend/tests/docker/fixtures/sample-h264-ac3.m2ts` in a loop at roughly real time (188-byte packets, ~500 KB/s), `GET /ace/stat/x/s` → `{response: {status: 'dl', peers: 3, speed_down: 500, speed_up: 0}}`, `GET /ace/cmd/x/s?method=stop` → 200.

`e2e/src/pages/integrations.ts`: `IntegrationsPage extends AppShell` with `open()`, `publicAddressSection()`, `playerCard(name)`, `serverCard(name)`, `addPlayer(fields)`, `testConnection()`, `expectProbe(text)`, `deletePlayer(name)`.

`e2e/tests/10-integrations.spec.ts`:
1. Page loads with the four sections and the public address StatusLine item.
2. Remote player: start a tiny Node HTTP server in the spec that answers `/requests/status.json` with 403; add a player pointing at `host.docker.internal`/`127.0.0.1:<port>`, click Test connection, expect the guided "web interface has no password" text; delete it through the menu + confirm.
3. Tuner endpoints: `api.raw('get', '/tuner/discover.json')` is JSON with `ModelNumber HDTC-2US`; `/tuner/nope` is JSON 404 (not HTML).
4. Deterministic playback: skip with an annotation when `GET /api/v1/player/capabilities` reports no ffmpeg; else start the stub engine, `api.putSetting('ace_engine_url', stubUrl)`, open Acestream Channels, `playChannel(<scenario channel>)`, expect the dialog status to reach "Playing" within 60 s and `video.readyState >= 2` (via `page.evaluate`), close; restore `ace_engine_url` in `finally`.
5. Real engine (tolerant): `playChannel` against the stack engine; accept "Playing" or an engine error Alert; annotate the outcome.

`e2e/stack/backend-start.sh`: `export FFMPEG_BINARY_PATH="${FFMPEG_BINARY_PATH:-$(command -v ffmpeg || true)}"`. Run `cd e2e && npx tsc --noEmit -p .` (or the project's lint) to validate; run the journey only if the stack is up (`npm run stack:up` + `npm run backend:start`), and report which parts executed.

- [ ] **Step 4: Regenerate and run everything**

```bash
backend/venv/bin/python backend/scripts/dump_openapi.py && cd frontend && npm run codegen && cd ..
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests --ignore=backend/tests/docker
cd frontend && npm run lint -- --max-warnings=0 && npm run typecheck && CI=true npm test -- --watch=false && npm run build && cd ..
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/validate_command_builder.sh && python3 scripts/ci/validate_docker_manifest_metadata.py && bash scripts/ci/publish_wiki.sh --dry-run
python3 scripts/ci/validate_docker_docs_contract.py
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add wiki/Media-Servers.md wiki/Home.md wiki/Configuration.md docs/ops/reverse-proxy.md README.md CLAUDE.md backend/openapi.json frontend/src/types/api-generated.ts backend/tests/contracts/test_integrations_contracts.py e2e/src/stub-engine.ts e2e/src/pages/integrations.ts e2e/tests/10-integrations.spec.ts e2e/stack/backend-start.sh e2e/scenarios/default.json e2e/src/scenario/schema.ts
git commit -m "docs(integrations): Jellyfin/Plex guide, reverse-proxy tuner rules, contracts and the e2e journey"
```

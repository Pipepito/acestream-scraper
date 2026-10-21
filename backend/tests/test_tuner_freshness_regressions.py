"""Freshness ranking through persisted data and the streaming route."""
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from app.models.models import AcestreamChannel, TVChannel
from app.services import tuner_service
from app.services.tuner_service import TunerService

NOW = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW if tz else NOW.replace(tzinfo=None)
    monkeypatch.setattr(tuner_service, "datetime", Clock)
    monkeypatch.setattr("app.services.tuner_playback_service._failures", OrderedDict())


@pytest.fixture
def allow_all_tuner_networks(monkeypatch):
    from app.config.settings import get_settings
    from app.services.tuner_network import get_tuner_gate
    try:
        with monkeypatch.context() as scoped:
            scoped.setenv("TUNER_ALLOWED_NETWORKS", "*")
            get_settings.cache_clear()
            get_tuner_gate.cache_clear()
            yield
    finally:
        # Restore the environment before clearing caches: client teardown can
        # resolve settings again, and must not retain this test's wildcard.
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()


def seed(db, rows):
    tv = TVChannel(name="Freshness test", is_active=True)
    db.add(tv)
    db.flush()
    for key, online, checked, bitrate in rows:
        db.add(AcestreamChannel(id=key * 40, name=key, tv_channel_id=tv.id,
                                is_active=True, is_online=online,
                                last_checked=checked, bitrate_bps=bitrate))
    db.commit()
    return tv


@pytest.mark.parametrize("checked,eligible", [
    (NOW - timedelta(hours=5, minutes=59), False),
    (NOW - timedelta(hours=6), False),
    (NOW - timedelta(hours=6, microseconds=1), True),
    ((NOW - timedelta(hours=1)).replace(tzinfo=None), False),
    (NOW + timedelta(hours=1), True),
    (None, True),
])
def test_only_recent_past_offline_observations_exclude_source(db_session, checked, eligible):
    tv = seed(db_session, [("a", False, checked, 1)])
    assert bool(TunerService(db_session).relay_stream_ids(tv.id)) is eligible


def test_future_timestamp_does_not_outrank_verified_recent_source(db_session):
    tv = seed(db_session, [("a", True, NOW + timedelta(days=1), 100),
                           ("b", True, NOW - timedelta(minutes=1), 1)])
    service = TunerService(db_session)
    assert service.online_stream_ids(tv.id) == ["b" * 40, "a" * 40]
    assert service.relay_stream_ids(tv.id) == ["b" * 40, "a" * 40]


def test_recent_unknown_remains_eligible_but_inactive_invalid_and_duplicates_do_not(db_session):
    tv = seed(db_session, [("a", None, NOW, 1), ("A", None, NOW, 1),
                           ("b", True, NOW, 100), ("x", True, NOW, 100)])
    db_session.get(AcestreamChannel, "b" * 40).is_active = False
    db_session.commit()
    service = TunerService(db_session)
    assert service.relay_stream_ids(tv.id) == ["a" * 40]
    tv.is_active = False
    db_session.commit()
    assert service.relay_stream_ids(tv.id) == []


def test_recent_relay_failure_still_overrides_freshness(alembic_db_session):
    from app.api.endpoints.tuner import _channel_candidates
    from app.services.tuner_playback_service import record_source_failure
    tv = seed(alembic_db_session, [("a", True, NOW, 100),
                                   ("b", True, NOW - timedelta(days=1), 1)])
    record_source_failure("a" * 40)
    assert _channel_candidates(tv.id) == ["b" * 40, "a" * 40]


@pytest.mark.parametrize("all_recent_offline", [False, True])
def test_streaming_route_uses_freshness_and_releases_claim(
    alembic_client, alembic_db_session, monkeypatch, all_recent_offline, allow_all_tuner_networks
):
    from app.api.endpoints import tuner
    from app.services.stream_relay import EngineStreamError, relay_registry
    import app.services.tuner_playback_service as playback
    tv = seed(alembic_db_session, [
        ("a", not all_recent_offline, NOW - timedelta(minutes=1), 10),
        ("b", False, NOW - timedelta(hours=1 if all_recent_offline else 12), 100),
        ("c", False, NOW - timedelta(minutes=1), 1000),
    ])
    attempts, cleaned = [], []
    engine = Mock()
    engine_factory = Mock(return_value=engine)
    monkeypatch.setattr(tuner, "_engine", engine_factory)
    monkeypatch.setattr(tuner.tuner_probe_service, "start", Mock(return_value=None))

    async def relay(_engine, content_id, *args, **kwargs):
        attempts.append(content_id)
        assert relay_registry.count_active() == 1
        try:
            if content_id == "a" * 40:
                raise EngineStreamError("source unavailable")
            yield b"\x47" + bytes(187)
        finally:
            cleaned.append(content_id)
    monkeypatch.setattr(playback, "relay_engine_stream", relay)
    try:
        url = f"/tuner/channel/{tv.id}.ts"
        assert alembic_client.head(url).status_code == 200
        engine_factory.assert_not_called()
        tuner.tuner_probe_service.start.assert_not_called()
        response = alembic_client.get(url)
        if all_recent_offline:
            assert response.status_code == 502
            assert attempts == []
        else:
            assert response.status_code == 200
            assert response.content == b"\x47" + bytes(187)
            assert attempts == ["a" * 40, "b" * 40]
        assert cleaned == attempts
        assert relay_registry.count_active() == 0
    finally:
        for claim in relay_registry.active():
            relay_registry.close(claim.id)

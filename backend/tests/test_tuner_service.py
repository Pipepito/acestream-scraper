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


@pytest.mark.parametrize("device_id", ["10E1F2F8", "12345674"])
def test_known_valid_ids(device_id):
    # 12345674: nibbles 1,2,3,4,5,6,7,4 -> lookup[1]^2^lookup[3]^4^lookup[5]^6^lookup[7]^4
    #           = 5^2^6^4^C^6^B^4 = 0
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

"""Tuner guide/playlist exports and the EPG export refactor they share (spec 7.2)."""
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

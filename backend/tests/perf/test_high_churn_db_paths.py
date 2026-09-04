"""
Performance regression guards for phase 6 high-churn DB paths.
"""
from contextlib import contextmanager

from sqlalchemy import event

from app.models.models import AcestreamChannel, EPGSource, ScrapedURL
from app.repositories.channel_repository import ChannelRepository
from app.repositories.url_repository import URLRepository
from app.services.epg_service import EPGService


def _build_epg_xml(channel_count: int, programs_per_channel: int) -> bytes:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<tv>"]
    for channel_idx in range(channel_count):
        lines.append(f'  <channel id="ch-{channel_idx}">')
        lines.append(f"    <display-name>Channel {channel_idx}</display-name>")
        lines.append("  </channel>")
    for channel_idx in range(channel_count):
        for program_idx in range(programs_per_channel):
            start_hour = program_idx % 24
            end_hour = (program_idx + 1) % 24
            lines.append(
                f'  <programme channel="ch-{channel_idx}" start="20260101{start_hour:02}0000 +0000" '
                f'stop="20260101{end_hour:02}0000 +0000">'
            )
            lines.append(f"    <title>Program {channel_idx}-{program_idx}</title>")
            lines.append("  </programme>")
    lines.append("</tv>")
    return "\n".join(lines).encode("utf-8")


@contextmanager
def _query_counter(db_session):
    engine = db_session.get_bind()
    count = {"value": 0}

    def before_cursor_execute(*_args, **_kwargs):
        count["value"] += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield count
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def test_bulk_activate_channels_query_budget(db_session):
    repo = ChannelRepository(db_session)
    channel_ids = [f"perf-channel-{idx}" for idx in range(200)]
    channels = [
        AcestreamChannel(
            id=channel_id,
            name=f"Perf Channel {idx}",
            source_url="https://example.com/perf.m3u",
            is_active=True,
        )
        for idx, channel_id in enumerate(channel_ids)
    ]
    db_session.add_all(channels)
    db_session.commit()

    with _query_counter(db_session) as counter:
        repo.bulk_activate_channels(channel_ids, active=False)

    assert counter["value"] <= 3


def test_refresh_all_urls_query_budget(db_session):
    repo = URLRepository(db_session)
    urls = [
        ScrapedURL(
            url=f"https://example.com/perf-{idx}.m3u",
            url_type="regular",
            status="active",
            enabled=True,
        )
        for idx in range(200)
    ]
    db_session.add_all(urls)
    db_session.commit()

    with _query_counter(db_session) as counter:
        refreshed = repo.refresh_all_urls()

    assert refreshed == 200
    assert counter["value"] <= 2


def test_repeat_epg_processing_query_budget(db_session):
    service = EPGService(db_session)
    source = EPGSource(url="https://example.com/perf-epg.xml", name="Perf Source", enabled=True)
    db_session.add(source)
    db_session.commit()

    payload = _build_epg_xml(channel_count=12, programs_per_channel=16)
    service._process_epg_xml(source.id, payload)

    with _query_counter(db_session) as counter:
        channels_found, programs_found = service._process_epg_xml(source.id, payload)

    assert channels_found == 0
    assert programs_found == 0
    assert counter["value"] <= 5

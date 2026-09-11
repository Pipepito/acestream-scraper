#!/usr/bin/env python3
"""
Phase 6 profiling harness for high-churn database paths.
"""
import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]
try:
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
except ModuleNotFoundError as exc:
    fallback_python = ROOT / "v2" / "backend" / "venv" / "bin" / "python"
    if exc.name == "sqlalchemy" and fallback_python.exists() and Path(sys.executable) != fallback_python:
        os.execv(str(fallback_python), [str(fallback_python), __file__, *sys.argv[1:]])
    raise

sys.path.insert(0, str(ROOT / "backend"))

from app.config.database import Base  # noqa: E402
from app.models.models import AcestreamChannel, EPGSource, ScrapedURL  # noqa: E402
from app.repositories.channel_repository import ChannelRepository  # noqa: E402
from app.repositories.url_repository import URLRepository  # noqa: E402
from app.services.epg_service import EPGService  # noqa: E402


def build_sample_epg_xml(channel_count: int, programs_per_channel: int) -> bytes:
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
            lines.append(f"    <desc>Description {channel_idx}-{program_idx}</desc>")
            lines.append("  </programme>")
    lines.append("</tv>")
    return "\n".join(lines).encode("utf-8")


@contextmanager
def query_counter(engine):
    counter = {"count": 0}

    def before_cursor_execute(*_args, **_kwargs):
        counter["count"] += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield counter
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


def profile() -> Dict[str, Dict[str, float]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    metrics: Dict[str, Dict[str, float]] = {}

    try:
        channel_repo = ChannelRepository(session)
        url_repo = URLRepository(session)
        epg_service = EPGService(session)

        channel_ids = [f"bulk-channel-{index}" for index in range(300)]
        channels = [
            AcestreamChannel(
                id=channel_id,
                name=f"Bulk Channel {index}",
                source_url="https://example.com/bulk.m3u",
                is_active=True,
            )
            for index, channel_id in enumerate(channel_ids)
        ]
        session.add_all(channels)
        session.commit()

        urls = [
            ScrapedURL(
                url=f"https://example.com/{index}.m3u",
                url_type="regular",
                status="active",
                enabled=True,
            )
            for index in range(300)
        ]
        session.add_all(urls)
        session.commit()

        source = EPGSource(url="https://example.com/epg.xml", name="Profile Source", enabled=True)
        session.add(source)
        session.commit()

        xml_payload = build_sample_epg_xml(channel_count=24, programs_per_channel=24)
        epg_service._process_epg_xml(source.id, xml_payload)

        with query_counter(engine) as channel_count:
            start = time.perf_counter()
            channel_repo.bulk_activate_channels(channel_ids, active=False)
            duration = time.perf_counter() - start
        metrics["bulk_activate_channels"] = {
            "duration_ms": round(duration * 1000, 2),
            "query_count": channel_count["count"],
        }

        with query_counter(engine) as refresh_count:
            start = time.perf_counter()
            refreshed = url_repo.refresh_all_urls()
            duration = time.perf_counter() - start
        metrics["refresh_all_urls"] = {
            "duration_ms": round(duration * 1000, 2),
            "query_count": refresh_count["count"],
            "rows": refreshed,
        }

        with query_counter(engine) as epg_count:
            start = time.perf_counter()
            channels_found, programs_found = epg_service._process_epg_xml(source.id, xml_payload)
            duration = time.perf_counter() - start
        metrics["process_epg_xml_repeat"] = {
            "duration_ms": round(duration * 1000, 2),
            "query_count": epg_count["count"],
            "channels_found": channels_found,
            "programs_found": programs_found,
        }

        return metrics
    finally:
        session.close()
        engine.dispose()


def parse_args():
    parser = argparse.ArgumentParser(description="Profile phase 6 high-churn DB paths.")
    parser.add_argument("--scenario", choices=["baseline", "optimized"], default="baseline")
    parser.add_argument("--json-output", type=Path, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    metrics = profile()
    payload = {
        "scenario": args.scenario,
        "generated_at": int(time.time()),
        "metrics": metrics,
    }

    if args.json_output:
        args.json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote profile results to {args.json_output}")

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

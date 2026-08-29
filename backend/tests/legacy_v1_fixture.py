"""Builders for synthetic v1 (``acestream.db``) SQLite fixtures.

The v1 schema is reconstructed from the columns ``migrate_database.py`` reads;
only what the migrator touches is modelled. Used by the migrator unit tests and
the startup regression tests so both exercise the same legacy layout.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

V1_SCHEMA = """
CREATE TABLE scraped_urls(
    id INTEGER PRIMARY KEY, url TEXT, status TEXT, last_processed TEXT, url_type TEXT,
    error_count INTEGER, last_error TEXT, enabled INTEGER, added_at TEXT
);
CREATE TABLE epg_sources(
    id INTEGER PRIMARY KEY, url TEXT, name TEXT, enabled INTEGER, last_updated TEXT,
    error_count INTEGER, last_error TEXT
);
CREATE TABLE tv_channels(
    id INTEGER PRIMARY KEY, name TEXT, description TEXT, logo_url TEXT, category TEXT,
    country TEXT, language TEXT, website TEXT, epg_id TEXT, epg_source_id INTEGER,
    created_at TEXT, updated_at TEXT, is_active INTEGER, is_favorite INTEGER, channel_number INTEGER
);
CREATE TABLE epg_channels(
    id INTEGER PRIMARY KEY, epg_source_id INTEGER, channel_xml_id TEXT, name TEXT,
    icon_url TEXT, language TEXT, created_at TEXT, updated_at TEXT
);
CREATE TABLE acestream_channels(
    id TEXT PRIMARY KEY, name TEXT, "group" TEXT, logo TEXT, tvg_id TEXT, tvg_name TEXT,
    source_url TEXT, added_at TEXT, last_processed TEXT, status TEXT, is_online INTEGER,
    last_checked TEXT, check_error TEXT, original_url TEXT, epg_update_protected INTEGER,
    tv_channel_id INTEGER
);
CREATE TABLE epg_programs(
    id INTEGER PRIMARY KEY, epg_channel_id INTEGER, program_xml_id TEXT, start_time TEXT,
    end_time TEXT, title TEXT, subtitle TEXT, description TEXT, category TEXT, icon_url TEXT
);
CREATE TABLE epg_string_mappings(
    id INTEGER PRIMARY KEY, epg_channel_id TEXT, search_pattern TEXT, is_exclusion INTEGER
);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
"""

BASE_TIME = datetime(2026, 8, 29, 12, 0, 0)


def create_v1_database(
    path: Path,
    *,
    channels: int = 3,
    programs_per_channel: int = 5,
    orphan_programs: int = 0,
) -> int:
    """Write a v1 database at ``path`` and return the number of EPG programs.

    ``orphan_programs`` adds programs that point at a non-existent EPG channel;
    the migrator must skip them because v2 requires ``epg_channel_id``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        cur = conn.cursor()
        cur.executescript(V1_SCHEMA)
        stamp = BASE_TIME.isoformat(sep=" ")
        cur.execute(
            "INSERT INTO scraped_urls VALUES(1, 'http://example.com/list', 'ok', ?, 'regular', 0, NULL, 1, ?)",
            (stamp, stamp),
        )
        cur.execute(
            "INSERT INTO epg_sources VALUES(1, 'http://example.com/epg.xml', 'Main', 1, ?, 0, NULL)",
            (stamp,),
        )
        for index in range(1, channels + 1):
            # v1 ids deliberately do not start at 1 so the tests catch any
            # assumption that v1 and v2 ids line up.
            v1_id = index * 10
            cur.execute(
                "INSERT INTO tv_channels VALUES(?, ?, NULL, NULL, 'General', 'ES', 'es', NULL, ?, 1, ?, ?, 1, 0, ?)",
                (v1_id, f"Channel {index}", f"ch{index}.example", stamp, stamp, index),
            )
            cur.execute(
                "INSERT INTO epg_channels VALUES(?, 1, ?, ?, NULL, 'es', ?, ?)",
                (v1_id, f"ch{index}.example", f"Channel {index}", stamp, stamp),
            )
            cur.execute(
                "INSERT INTO acestream_channels VALUES(?, ?, 'General', NULL, ?, ?, 'http://example.com/list', ?, ?, 'active', 1, ?, NULL, NULL, 0, ?)",
                (f"{index:040x}", f"Channel {index}", f"ch{index}.example", f"Channel {index}", stamp, stamp, stamp, v1_id),
            )
        cur.execute("INSERT INTO epg_string_mappings VALUES(1, 'ch1.example', 'Channel 1', 0)")
        cur.execute("INSERT INTO settings VALUES('base_url', 'acestream://')")

        rows = []
        for index in range(1, channels + 1):
            for offset in range(programs_per_channel):
                start = BASE_TIME + timedelta(minutes=30 * offset)
                end = start + timedelta(minutes=30)
                rows.append(
                    (
                        index * 10,
                        f"p{index}-{offset}",
                        start.isoformat(sep=" "),
                        end.isoformat(sep=" "),
                        f"Show {index}-{offset}",
                        None,
                        "Synthetic description",
                        "Series",
                        None,
                    )
                )
        for offset in range(orphan_programs):
            start = BASE_TIME + timedelta(hours=offset)
            rows.append((999_999, f"orphan-{offset}", start.isoformat(sep=" "), (start + timedelta(hours=1)).isoformat(sep=" "), "Orphan", None, None, None, None))
        cur.executemany(
            "INSERT INTO epg_programs(epg_channel_id, program_xml_id, start_time, end_time, title, subtitle, description, category, icon_url) VALUES(?,?,?,?,?,?,?,?,?)",
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def count_rows(path: Path, table: str) -> int:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()

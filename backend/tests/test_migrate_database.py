"""v1 -> v2 migrator: fast foreground phase + resumable deferred EPG programs.

Regression suite for the unraid report where startup blocked on copying every
EPG program before uvicorn would answer, leaving the container unhealthy. The
migrator now copies the small tables synchronously, archives the v1 file, and
records the EPG programs as deferred work that runs as a background task.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from tests.legacy_v1_fixture import BASE_TIME, count_rows, create_v1_database


@pytest.fixture
def legacy_runtime(tmp_path, monkeypatch):
    """Bind settings + engine to a temp v2 db and a synthetic v1 db path."""
    from app.config import database as database_module
    from app.config import settings as settings_module

    v2_path = tmp_path / "config" / "scraper.db"
    v1_path = tmp_path / "config" / "acestream.db"
    v2_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{v2_path.as_posix()}")
    monkeypatch.setenv("LEGACY_DATABASE_URL", f"sqlite:///{v1_path.as_posix()}")
    settings_module.get_settings.cache_clear()
    settings_module.settings = settings_module.get_settings()
    database_module.reset_engine()
    try:
        yield {"v1": v1_path, "v2": v2_path}
    finally:
        database_module.reset_engine()
        settings_module.get_settings.cache_clear()
        settings_module.settings = settings_module.get_settings()


def _migrator(batch_size: int = 4):
    from migrate_database import DatabaseMigrator

    return DatabaseMigrator(batch_size=batch_size)


def _state(migrator) -> dict:
    return json.loads(Path(migrator.state_path).read_text(encoding="utf-8"))


def _table_names(db_path: Path) -> set[str]:
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_foreground_migration_defers_epg_programs(legacy_runtime):
    total = create_v1_database(legacy_runtime["v1"], channels=3, programs_per_channel=5)
    migrator = _migrator()

    assert migrator.should_migrate() is True
    assert migrator.run_migration() is True

    v2 = legacy_runtime["v2"]
    assert count_rows(v2, "epg_channels") == 3
    assert count_rows(v2, "acestream_channels") == 3
    assert count_rows(v2, "epg_string_mappings") == 1
    assert count_rows(v2, "settings") >= 1
    # The expensive table is NOT copied in the foreground phase.
    assert count_rows(v2, "epg_programs") == 0

    assert not legacy_runtime["v1"].exists()
    assert Path(migrator.v1_migrated_path).exists()
    assert migrator.should_migrate() is False
    assert migrator.has_deferred_work() is True

    state = _state(migrator)
    programs = state["epg_programs"]
    assert programs["status"] == "pending"
    assert programs["total"] == total
    assert programs["last_v1_id"] == 0
    # v1 epg_channel ids (10, 20, 30) map onto the freshly inserted v2 ids.
    assert set(programs["epg_channel_ids"]) == {"10", "20", "30"}


def test_foreground_migration_stamps_schema_with_alembic(legacy_runtime):
    create_v1_database(legacy_runtime["v1"], channels=1, programs_per_channel=1)
    _migrator().run_migration()

    assert "alembic_version" in _table_names(legacy_runtime["v2"]), (
        "v1-migrated databases must be provisioned through Alembic so later revisions apply"
    )


def test_deferred_migration_copies_programs_and_marks_done(legacy_runtime):
    total = create_v1_database(legacy_runtime["v1"], channels=3, programs_per_channel=5, orphan_programs=2)
    migrator = _migrator(batch_size=4)
    migrator.run_migration()

    seen = []
    summary = migrator.run_deferred_migration(progress=seen.append)

    assert summary["status"] == "done"
    assert summary["migrated"] == 15
    assert summary["skipped"] == 2
    assert summary["total"] == total
    assert count_rows(legacy_runtime["v2"], "epg_programs") == 15
    assert seen, "progress callback should fire at least once per batch"
    assert seen[-1]["migrated"] == 15
    assert migrator.has_deferred_work() is False
    assert _state(migrator)["epg_programs"]["status"] == "done"

    conn = sqlite3.connect(str(legacy_runtime["v2"]))
    try:
        channel_ids = {row[0] for row in conn.execute("SELECT DISTINCT epg_channel_id FROM epg_programs")}
        v2_channels = {row[0] for row in conn.execute("SELECT id FROM epg_channels")}
        image_urls = conn.execute("SELECT COUNT(*) FROM epg_programs WHERE title LIKE 'Show %'").fetchone()[0]
    finally:
        conn.close()
    assert channel_ids == v2_channels
    assert image_urls == 15


def test_deferred_migration_resumes_from_checkpoint_without_duplicates(legacy_runtime):
    create_v1_database(legacy_runtime["v1"], channels=3, programs_per_channel=5)
    migrator = _migrator(batch_size=4)
    migrator.run_migration()

    stop = threading.Event()

    def stop_after_first_batch(progress):
        stop.set()

    first = migrator.run_deferred_migration(progress=stop_after_first_batch, stop_event=stop)
    assert first["status"] == "interrupted"
    assert 0 < first["migrated"] < 15
    checkpoint = _state(migrator)["epg_programs"]
    assert checkpoint["status"] == "running"
    assert checkpoint["last_v1_id"] > 0
    assert migrator.has_deferred_work() is True

    second = _migrator(batch_size=4).run_deferred_migration()
    assert second["status"] == "done"
    assert second["migrated"] == 15
    assert count_rows(legacy_runtime["v2"], "epg_programs") == 15


def test_deferred_migration_does_not_duplicate_programs_already_in_v2(legacy_runtime):
    create_v1_database(legacy_runtime["v1"], channels=1, programs_per_channel=3)
    migrator = _migrator()
    migrator.run_migration()

    # Simulate the hourly EPG refresh having inserted one of the programs
    # before the deferred copy ran (same channel/start/end/title).
    v1_rows = sqlite3.connect(migrator.v1_migrated_path).execute(
        "SELECT start_time, end_time, title FROM epg_programs ORDER BY id LIMIT 1"
    ).fetchone()
    conn = sqlite3.connect(str(legacy_runtime["v2"]))
    try:
        v2_channel = conn.execute("SELECT id FROM epg_channels").fetchone()[0]
        conn.execute(
            "INSERT INTO epg_programs(epg_channel_id, start_time, end_time, title) VALUES(?,?,?,?)",
            (v2_channel, *v1_rows),
        )
        conn.commit()
    finally:
        conn.close()

    summary = migrator.run_deferred_migration()
    assert summary["status"] == "done"
    assert summary["migrated"] == 2
    assert count_rows(legacy_runtime["v2"], "epg_programs") == 3


def test_deferred_migration_marks_error_when_archive_is_missing(legacy_runtime):
    create_v1_database(legacy_runtime["v1"], channels=1, programs_per_channel=2)
    migrator = _migrator()
    migrator.run_migration()
    Path(migrator.v1_migrated_path).unlink()

    with pytest.raises(FileNotFoundError):
        migrator.run_deferred_migration()

    state = _state(migrator)["epg_programs"]
    assert state["status"] == "error"
    assert "acestream.db.migrated" in (state["error"] or "")
    # Missing archive is permanent: don't retry on every boot.
    assert migrator.has_deferred_work() is False


def test_migration_without_programs_leaves_no_deferred_work(legacy_runtime):
    create_v1_database(legacy_runtime["v1"], channels=2, programs_per_channel=0)
    migrator = _migrator()
    migrator.run_migration()

    assert migrator.has_deferred_work() is False
    assert not Path(migrator.state_path).exists()


def test_deferred_run_is_noop_when_nothing_pending(legacy_runtime):
    migrator = _migrator()
    assert migrator.has_deferred_work() is False
    assert migrator.run_deferred_migration()["status"] == "done"


def test_background_task_id_matches_migrator_constant():
    from app.tasks.legacy_migration_task import TASK_ID
    from migrate_database import DatabaseMigrator

    assert TASK_ID == DatabaseMigrator.DEFERRED_TASK_ID == "v1_epg_programs_migration"


def test_deferred_migration_skips_programs_that_already_ended(legacy_runtime):
    # Fixture programs per channel: 12:00-12:30, 12:30-13:00, 13:00-13:30, 13:30-14:00, 14:00-14:30.
    total = create_v1_database(legacy_runtime["v1"], channels=2, programs_per_channel=5)
    from migrate_database import DatabaseMigrator

    now = BASE_TIME.replace(tzinfo=timezone.utc) + timedelta(hours=4)  # 16:00 -> cutoff 14:00
    migrator = DatabaseMigrator(batch_size=3, epg_retention_hours=2, now=now)
    migrator.run_migration()

    summary = migrator.run_deferred_migration()

    assert summary["status"] == "done"
    assert summary["migrated"] == 4, "only programs ending at/after the cutoff (14:00, 14:30) per channel"
    assert summary["stale"] == 6
    assert summary["skipped"] == 0
    assert summary["processed"] == summary["total"] == total
    assert summary["percent"] == 100.0
    assert count_rows(legacy_runtime["v2"], "epg_programs") == 4
    assert _state(migrator)["epg_programs"]["stale_cutoff"] == "2026-08-29 14:00:00"


def test_deferred_migration_keeps_everything_when_retention_is_disabled(legacy_runtime):
    total = create_v1_database(legacy_runtime["v1"], channels=2, programs_per_channel=5)
    from migrate_database import DatabaseMigrator

    now = BASE_TIME.replace(tzinfo=timezone.utc) + timedelta(days=30)
    migrator = DatabaseMigrator(epg_retention_hours=-1, now=now)
    migrator.run_migration()

    summary = migrator.run_deferred_migration()

    assert summary["migrated"] == total
    assert summary["stale"] == 0
    assert _state(migrator)["epg_programs"]["stale_cutoff"] is None


def test_retention_defaults_to_settings(legacy_runtime, monkeypatch):
    from app.config import settings as settings_module

    monkeypatch.setenv("EPG_PROGRAM_RETENTION_HOURS", "2.5")
    settings_module.get_settings.cache_clear()
    try:
        assert _migrator().epg_retention_hours == 2.5
    finally:
        settings_module.get_settings.cache_clear()

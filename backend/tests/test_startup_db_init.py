import json
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

from tests.legacy_v1_fixture import count_rows, create_v1_database


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"


def _database_url_for(db_path: Path) -> str:
    return f"sqlite:///{db_path.resolve().as_posix()}"


def _run_main_import(
    database_url: str,
    frontend_build_path: Path,
    legacy_database_url: str,
    extra_pythonpath: list[Path] | None = None,
    boot_script: str | None = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Boot ``main.app`` through its lifespan so DB init actually runs.

    ``initialize_database()`` lives inside the FastAPI ``lifespan`` context
    manager (see ``backend/main.py``); a bare ``import main`` no longer triggers
    it. Driving the lifespan via ``TestClient`` as a context manager exercises
    the same startup path used by ``uvicorn`` in production.
    """
    frontend_build_path.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    pythonpath_entries = [str(path) for path in extra_pythonpath or []]
    pythonpath_entries.append(str(BACKEND_ROOT))

    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)

    env.update(
        {
            "DATABASE_URL": database_url,
            "LEGACY_DATABASE_URL": legacy_database_url,
            # The v1 fixture carries fixed 2026-08-29 timestamps; disable retention so the
            # deferred copy is not skipped as "stale" once real time moves past the window.
            "EPG_PROGRAM_RETENTION_HOURS": "-1",
            "FRONTEND_BUILD_PATH": str(frontend_build_path),
            "PYTHONPATH": os.pathsep.join(pythonpath_entries),
        }
    )

    boot_script = boot_script or (
        "import main\n"
        "from fastapi.testclient import TestClient\n"
        "with TestClient(main.app):\n"
        "    pass\n"
    )

    return subprocess.run(
        [sys.executable, "-c", boot_script],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _inspect_tables(db_path: Path) -> set[str]:
    engine = create_engine(_database_url_for(db_path))
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_fresh_db_startup_applies_migrations_instead_of_create_all(tmp_path):
    db_path = tmp_path / "startup.db"
    legacy_db_path = tmp_path / "legacy.db"

    result = _run_main_import(
        database_url=_database_url_for(db_path),
        legacy_database_url=_database_url_for(legacy_db_path),
        frontend_build_path=tmp_path / "frontend-build",
    )

    assert result.returncode == 0, (
        "Expected startup import to succeed for a fresh database.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    tables = _inspect_tables(db_path)

    assert "alembic_version" in tables, (
        "Expected fresh startup to provision the database through Alembic so the schema is "
        f"stamped with `alembic_version`, but startup created tables without it. Tables: {sorted(tables)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_startup_surfaces_migration_failure_without_create_all_fallback(tmp_path):
    db_path = tmp_path / "startup.db"
    legacy_db_path = tmp_path / "legacy.db"
    override_dir = tmp_path / "override"
    override_dir.mkdir()
    (override_dir / "migrate_database.py").write_text(
        "class DatabaseMigrator:\n"
        "    def __init__(self):\n"
        "        self.v2_db_path = 'unused.db'\n\n"
        "    def should_migrate(self):\n"
        "        return True\n\n"
        "    def run_migration(self):\n"
        "        raise RuntimeError('forced migration failure for startup test')\n",
        encoding="ascii",
    )

    result = _run_main_import(
        database_url=_database_url_for(db_path),
        legacy_database_url=_database_url_for(legacy_db_path),
        frontend_build_path=tmp_path / "frontend-build",
        extra_pythonpath=[override_dir],
    )

    assert result.returncode != 0, (
        "Expected startup import to fail loudly when migrations fail instead of silently "
        "falling back to `create_all(...)`.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    tables = _inspect_tables(db_path) if db_path.exists() else set()

    assert "settings" not in tables, (
        "Expected failed startup not to leave behind an application schema from emergency "
        f"`create_all(...)`, but found tables: {sorted(tables)}"
    )


V1_BOOT_SCRIPT = """
import json, time
import main
from fastapi.testclient import TestClient

with TestClient(main.app) as client:
    health = client.get("/api/v1/health")
    print("HEALTH", health.status_code, health.json().get("status"))
    final = None
    deadline = time.time() + 20
    while time.time() < deadline:
        tasks = client.get("/api/v1/background-tasks/status").json()
        task = next((t for t in tasks if t["task_name"] == "v1_epg_programs_migration"), None)
        if task is not None and task["status"] in ("idle", "error"):
            final = task
            break
        time.sleep(0.1)
    print("TASK", json.dumps(final))
"""


def test_v1_startup_serves_requests_while_epg_programs_migrate_in_background(tmp_path):
    """Regression for the unraid report: startup blocked on copying every EPG
    program, so the dashboard was unreachable and the container unhealthy."""
    db_path = tmp_path / "config" / "scraper.db"
    legacy_db_path = tmp_path / "config" / "acestream.db"
    total = create_v1_database(legacy_db_path, channels=4, programs_per_channel=25, orphan_programs=3)

    result = _run_main_import(
        database_url=_database_url_for(db_path),
        legacy_database_url=_database_url_for(legacy_db_path),
        frontend_build_path=tmp_path / "frontend-build",
        boot_script=V1_BOOT_SCRIPT,
        timeout=60,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    lines = dict(line.split(" ", 1) for line in result.stdout.splitlines() if line.startswith(("HEALTH ", "TASK ")))
    assert lines["HEALTH"].startswith("200 healthy"), result.stdout

    task = json.loads(lines["TASK"])
    assert task is not None, f"background migration task never finished\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert task["status"] == "idle", task
    assert task["last_error"] is None
    assert task["last_result"]["status"] == "done"
    assert task["last_result"]["migrated"] == total - 3
    assert task["last_result"]["skipped"] == 3
    assert task["progress"]["percent"] == 100.0

    assert count_rows(db_path, "epg_programs") == total - 3
    assert count_rows(db_path, "epg_channels") == 4
    assert not legacy_db_path.exists()
    assert (tmp_path / "config" / "acestream.db.migrated").exists()
    state = json.loads((tmp_path / "config" / "acestream.db.migration.json").read_text(encoding="utf-8"))
    assert state["epg_programs"]["status"] == "done"
    assert "alembic_version" in _inspect_tables(db_path)


def test_startup_stamps_existing_unstamped_v2_database(tmp_path):
    """Databases created by the pre-fix migrator (``create_all``) carry no
    ``alembic_version``; startup must record the head so later revisions apply."""
    db_path = tmp_path / "config" / "scraper.db"
    db_path.parent.mkdir(parents=True)
    legacy_db_path = tmp_path / "config" / "acestream.db"

    from app.config.database import Base
    import app.models.models  # noqa: F401  (register every table on Base)

    engine = create_engine(_database_url_for(db_path))
    try:
        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()
    assert "alembic_version" not in _inspect_tables(db_path)

    result = _run_main_import(
        database_url=_database_url_for(db_path),
        legacy_database_url=_database_url_for(legacy_db_path),
        frontend_build_path=tmp_path / "frontend-build",
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "alembic_version" in _inspect_tables(db_path)
    assert "unstamped" in result.stdout

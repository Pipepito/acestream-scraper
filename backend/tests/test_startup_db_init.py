import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"


def _database_url_for(db_path: Path) -> str:
    return f"sqlite:///{db_path.resolve().as_posix()}"


def _run_main_import(
    database_url: str,
    frontend_build_path: Path,
    legacy_database_url: str,
    extra_pythonpath: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
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
            "FRONTEND_BUILD_PATH": str(frontend_build_path),
            "PYTHONPATH": os.pathsep.join(pythonpath_entries),
        }
    )

    return subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
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

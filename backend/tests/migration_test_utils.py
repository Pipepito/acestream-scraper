import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, inspect


REPO_ROOT = Path(__file__).resolve().parents[2]


def database_url_for(db_path: Path) -> str:
    return f"sqlite:///{db_path.resolve().as_posix()}"


def run_alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    db_path.touch()
    database_url = database_url_for(db_path)
    command = ['alembic', '-c', 'backend/migrations/alembic.ini', *args]
    env = os.environ.copy()
    env['DATABASE_URL'] = database_url
    env['PYTHONPATH'] = 'backend'
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _assert_alembic_success(result: subprocess.CompletedProcess[str], db_path: Path, *args: str) -> None:
    database_url = database_url_for(db_path)
    command_display = (
        f'DATABASE_URL="{database_url}" '
        'PYTHONPATH=backend '
        f"alembic -c backend/migrations/alembic.ini {' '.join(args)}"
    )
    assert result.returncode == 0, (
        'Alembic upgrade command failed unexpectedly.\n'
        f'Command: {command_display}\n'
        f'stdout:\n{result.stdout}\n'
        f'stderr:\n{result.stderr}'
    )


def upgrade_to_revision(db_path: Path, revision: str) -> None:
    result = run_alembic(db_path, 'upgrade', revision)
    _assert_alembic_success(result, db_path, 'upgrade', revision)


def upgrade_to_head(db_path: Path) -> None:
    result = run_alembic(db_path, 'upgrade', 'head')
    _assert_alembic_success(result, db_path, 'upgrade', 'head')


def downgrade_to_revision(db_path: Path, revision: str) -> None:
    result = run_alembic(db_path, 'downgrade', revision)
    _assert_alembic_success(result, db_path, 'downgrade', revision)


def upgraded_inspector(db_path: Path):
    upgrade_to_head(db_path)
    engine = create_engine(database_url_for(db_path))
    return engine, inspect(engine)

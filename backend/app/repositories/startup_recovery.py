"""Offline SQLite recovery. Originals remain in a private, unique backup folder.

Only called before application services start, under the process's data lock.
Recovery is staged through Alembic; no model create_all or replacement on failure.
"""
import json
import os
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic import command
from sqlalchemy.engine import make_url

from app.config.database import _alembic_config, reset_engine, Base
from app.config.settings import get_settings


class NoRecoverableDataError(RuntimeError):
    """No source rows can be retained; keep the original database installed."""


class InterruptedRecoveryError(RuntimeError):
    """A durable recovery marker says installation did not finish."""


def database_path():
    url = make_url(get_settings().DATABASE_URL)
    if url.drivername != 'sqlite' or not url.database or url.database == ':memory:':
        raise ValueError('Recovery requires a file-backed SQLite database')
    return Path(url.database).resolve()


def recovery_marker():
    return database_path().with_suffix('.recovery.json')


def legacy_disabled():
    marker = recovery_marker()
    if not marker.exists():
        return False
    state = json.loads(marker.read_text())
    if state['status'] != 'complete':
        raise InterruptedRecoveryError('An interrupted recovery needs attention')
    return True


def _write_marker(payload):
    marker = recovery_marker()
    temporary = marker.with_suffix('.tmp')
    with open(temporary, 'w') as handle:
        json.dump(payload, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, marker)
    _sync_directory(marker.parent)


PRIORITY_SOURCE_TABLES = ('scraped_urls', 'epg_sources')


def _source_values(name, values):
    """Retain source configuration without carrying broken operational metadata."""
    url = values.get('url')
    if not isinstance(url, str) or not url.strip():
        return None
    result = {
        'url': url,
        'enabled': values.get('enabled') not in (False, 0, '0', 'false', 'False'),
        'error_count': 0,
    }
    if values.get('id') is not None:
        result['id'] = values['id']
    if name == 'scraped_urls':
        result.update(
            url_type=values.get('url_type') or 'regular',
            scrape_bare_ids=values.get('scrape_bare_ids') in (True, 1, '1', 'true', 'True'),
            status='pending',
            added_at=datetime.now(timezone.utc).isoformat(),
        )
    else:
        source_name = values.get('name')
        result['name'] = source_name if isinstance(source_name, str) and source_name.strip() else 'Recovered EPG source'
    return result


def _copy_readable(source, target, report):
    """Recover source configuration first, then other tables in dependency order.

    Guide data and transient history are refreshed by the app, not salvaged.
    Values and SQL errors never enter the downloadable report.
    """
    import app.models.models  # noqa: F401
    excluded = {'epg_programs', 'activity_log', 'stream_sessions'}
    total_copied = 0
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as old, closing(sqlite3.connect(target)) as new:
        new.execute('PRAGMA foreign_keys=ON')
        tables = list(Base.metadata.sorted_tables)
        ordered = [Base.metadata.tables[name] for name in PRIORITY_SOURCE_TABLES]
        ordered.extend(table for table in tables if table.name not in PRIORITY_SOURCE_TABLES)
        report('Recovering scraper URLs and EPG sources first')
        for table in ordered:
            name = table.name
            if name in excluded:
                continue
            copied = skipped = 0
            unreadable = False
            try:
                columns = {row[1] for row in old.execute(f'PRAGMA table_info("{name}")')}
                shared = [column.name for column in table.columns if column.name in columns]
                if not shared:
                    continue
                quoted = ','.join('"' + col + '"' for col in shared)
                rows = old.execute(f'SELECT {quoted} FROM "{name}"')
            except sqlite3.DatabaseError:
                report(f'Could not read {name}; this table was skipped.', 'warning')
                continue
            while True:
                try:
                    batch = rows.fetchmany(500)
                except sqlite3.DatabaseError:
                    unreadable = True
                    break
                if not batch:
                    break
                for row in batch:
                    if name in PRIORITY_SOURCE_TABLES:
                        values = _source_values(name, dict(zip(shared, row)))
                        if values is None:
                            skipped += 1
                            continue
                        insert_columns = ','.join('"' + column + '"' for column in values)
                        insert_values = tuple(values.values())
                    else:
                        insert_columns, insert_values = quoted, row
                    try:
                        new.execute(f'INSERT INTO "{name}" ({insert_columns}) VALUES ({",".join("?" for _ in insert_values)})', insert_values)
                        copied += 1
                        total_copied += 1
                    except sqlite3.IntegrityError:
                        skipped += 1
                # Destination failures (disk full, I/O) must abort recovery;
                # they are not unreadable source rows that can be skipped.
                new.commit()
            report(f'Recovered {name}: {copied} rows; {skipped} skipped.')
            if unreadable:
                report(f'Some {name} data could not be read.', 'warning')
        if new.execute('PRAGMA foreign_key_check').fetchone():
            raise RuntimeError('Recovered database has broken references')
    if not total_copied:
        raise NoRecoverableDataError('No readable data was recovered. Original files are unchanged.')


def _recover_database(action, report, release_source):
    path = database_path()
    reset_engine()
    preserved_source = None
    source_backup = None
    if action == 'salvage' and recovery_marker().exists():
        state = json.loads(recovery_marker().read_text())
        if state.get('status') == 'pending':
            import re
            source_backup = state.get('source_backup', state.get('backup', ''))
            if not re.fullmatch(r'recovery-[0-9a-f]{32}', source_backup):
                raise RuntimeError('Invalid recovery backup reference')
            preserved_source = path.parent / 'backups' / source_backup / 'current' / path.name
            if not preserved_source.is_file():
                raise RuntimeError('The interrupted recovery backup is missing')
    backup = path.parent / 'backups' / ('recovery-' + uuid4().hex)
    backup.mkdir(parents=True, mode=0o700)
    report('Saving a backup of the current database and migration files')
    legacy = Path(make_url(get_settings().LEGACY_DATABASE_URL).database).resolve()
    # Keep raw files, including WAL, even if SQLite cannot read the database.
    # No scheduler, requests, or other app worker can write during recovery.
    groups = {
        'current': [path, *(Path(str(path) + suffix) for suffix in ('-wal', '-shm', '-journal')),
                    recovery_marker()],
        'legacy': [legacy, *(Path(str(legacy) + suffix) for suffix in
                            ('-wal', '-shm', '-journal', '.migrated', '.migrated-wal', '.migrated-shm', '.migration.json'))],
    }
    for group, sources in groups.items():
        directory = backup / group
        directory.mkdir(mode=0o700)
        for source in sources:
            if source.exists():
                destination = directory / source.name
                shutil.copyfile(source, destination)
                os.chmod(destination, 0o600)
                with open(destination, 'rb') as handle:
                    os.fsync(handle.fileno())
        _sync_directory(directory)
    _sync_directory(backup)
    _sync_directory(backup.parent)
    report('Backup saved: ' + backup.name)
    staged = backup / 'rebuilt.db'
    config = _alembic_config()
    config.attributes['database_url'] = 'sqlite:///' + str(staged)
    report('Creating a clean database')
    command.upgrade(config, 'head')
    if action == 'salvage':
        if not preserved_source and not path.exists():
            raise NoRecoverableDataError('No current database to recover')
        report('Recovering sources so channels and programme listings can be rebuilt')
        _copy_readable(preserved_source or backup / 'current' / path.name, staged, report)
    os.chmod(staged, 0o600)
    with closing(sqlite3.connect(staged)) as connection:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Recovered database did not pass verification')
    # Persist before any replacement. A crash keeps the next boot in recovery
    # instead of accidentally combining old checkpoints with new channel IDs.
    _write_marker({'status': 'pending', 'backup': backup.name, 'source_backup': source_backup or backup.name})
    release_source()
    for suffix in ('-wal', '-shm', '-journal'):
        Path(str(path) + suffix).unlink(missing_ok=True)
    with open(staged, 'rb') as handle:
        os.fsync(handle.fileno())
    os.replace(staged, path)
    _sync_directory(path.parent)
    _write_marker({'status': 'complete', 'backup': backup.name})
    report('Database rebuilt. Original files are saved in ' + backup.name)


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def recover_database(action, report):
    if action not in {'fresh', 'salvage'}:
        raise ValueError('Unsupported recovery action')
    path = database_path()
    legacy = Path(make_url(get_settings().LEGACY_DATABASE_URL).database).resolve()
    if path == legacy:
        raise ValueError('Legacy and current database paths must be different')
    reset_engine()
    connection = None
    try:
        if path.exists():
            connection = sqlite3.connect(path, timeout=1)
            try:
                # Block other SQLite writers while the source and its WAL are
                # copied. Salvage reads the backup, never the locked source.
                connection.execute('BEGIN IMMEDIATE')
            except sqlite3.DatabaseError as exc:
                if getattr(exc, 'sqlite_errorcode', None) not in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB):
                    raise
                connection.close()
                connection = None
        def release_source():
            nonlocal connection
            if connection is not None:
                connection.close()
                connection = None
        _recover_database(action, report, release_source)
    finally:
        if connection is not None:
            # No writes were made through this transaction. Close before any
            # subsequent boot opens the replacement database.
            connection.close()

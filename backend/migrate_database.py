"""
Database migration for Acestream Scraper v1 -> v2.

The migration runs in two phases so startup never blocks on the largest table:

* ``run_migration()`` — foreground (called from the FastAPI lifespan before the
  first request). Provisions the v2 schema through Alembic, copies the small
  tables (scraped URLs, EPG sources, TV/EPG/acestream channels, string mappings,
  settings), records the EPG programs as deferred work in
  ``<acestream.db>.migration.json`` and archives ``acestream.db`` as
  ``acestream.db.migrated``. This takes seconds even on slow storage.
* ``run_deferred_migration()`` — background (APScheduler one-off task
  ``v1_epg_programs_migration``). Copies EPG programs from the archived v1 file
  in batches with keyset pagination, deduplicating against rows the hourly EPG
  refresh may already have inserted, and checkpoints after every commit so a
  restart resumes where it stopped.
"""
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from threading import Event
from typing import Any, Callable, Dict, List, Optional

from app.config.database import provision_schema
from app.config.settings import get_settings


ProgressCallback = Callable[[Dict[str, Any]], None]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class DatabaseMigrator:
    #: Job id of the background task that copies EPG programs.
    DEFERRED_TASK_ID = "v1_epg_programs_migration"
    STATE_FORMAT = 1

    def __init__(self, batch_size: int = 2000):
        settings = get_settings()
        self.v1_db_path = settings.LEGACY_DATABASE_URL.replace("sqlite:///", "")
        self.v2_db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        self.v1_migrated_path = self.v1_db_path + ".migrated"
        self.state_path = self.v1_db_path + ".migration.json"
        self.batch_size = max(1, int(batch_size))

        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.v2_db_path) or ".", exist_ok=True)

        # Track ID mappings for foreign keys
        self.id_mappings = {
            'scraped_urls': {},     # old_id -> new_id
            'epg_sources': {},      # old_id -> new_id
            'tv_channels': {},      # old_id -> new_id
            'epg_channels': {},     # old_id -> new_id
        }

    def should_migrate(self) -> bool:
        """Check if the foreground migration should run"""
        return os.path.exists(self.v1_db_path) and not os.path.exists(self.v1_migrated_path)

    def inspect_v1_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Inspect v1 database structure and return table schemas"""
        if not os.path.exists(self.v1_db_path):
            print(f"V1 database not found at {self.v1_db_path}")
            return {}

        schemas = {}

        try:
            with sqlite3.connect(self.v1_db_path) as conn:
                cursor = conn.cursor()

                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                print(f"Found {len(tables)} tables in v1 database:")

                for table_name in tables:
                    table_name = table_name[0]
                    if table_name == 'alembic_version':
                        continue

                    print(f"\nTable: {table_name}")

                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()

                    table_schema = []
                    for col in columns:
                        col_info = {
                            'name': col[1],
                            'type': col[2],
                            'notnull': col[3],
                            'default': col[4],
                            'pk': col[5]
                        }
                        table_schema.append(col_info)
                        print(f"  - {col_info['name']}: {col_info['type']} (pk={col_info['pk']}, notnull={col_info['notnull']})")

                    schemas[table_name] = table_schema

                    # Show row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"  Rows: {count}")

        except Exception as e:
            print(f"Error inspecting v1 database: {e}")
            return {}

        return schemas

    def create_v2_database(self):
        """Provision the v2 schema through Alembic (same path as fresh installs).

        ``Base.metadata.create_all`` used to be called here, which left migrated
        databases without an ``alembic_version`` stamp and broke every later
        schema revision. ``provision_schema`` stamps such databases first.
        """
        print("Provisioning v2 database schema via Alembic...")
        state = provision_schema()
        if state == "unstamped":
            print("Existing v2 database was not stamped; recorded the current Alembic head")
        print("V2 database schema ready!")

    def update_v2_schema(self):
        """Update v2 database schema to add missing columns"""
        print("Updating v2 database schema...")

        try:
            v2_conn = sqlite3.connect(self.v2_db_path)
            v2_cursor = v2_conn.cursor()

            # Check if check_error column exists in acestream_channels
            v2_cursor.execute("PRAGMA table_info(acestream_channels);")
            columns = v2_cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Add check_error column if it doesn't exist
            if 'check_error' not in column_names:
                print("Adding check_error column to acestream_channels table...")
                v2_cursor.execute("""
                    ALTER TABLE acestream_channels
                    ADD COLUMN check_error TEXT
                """)
                v2_conn.commit()
                print("check_error column added successfully!")
            else:
                print("check_error column already exists in acestream_channels table")

            v2_conn.close()

        except Exception as e:
            print(f"Error updating v2 database schema: {e}")

    def migrate_scraped_urls(self):
        """Migrate scraped URLs first (needed for foreign keys)"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating scraped URLs...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scraped_urls';")
            if not v1_cursor.fetchone():
                print("scraped_urls table not found in v1 database")
                return

            v1_cursor.execute("SELECT * FROM scraped_urls ORDER BY id;")
            v1_urls = v1_cursor.fetchall()

            print(f"Found {len(v1_urls)} scraped URLs in v1 database")

            migrated_count = 0
            for row in v1_urls:
                try:
                    # Map v1 fields to v2 fields - handle missing columns safely
                    url_type = row['url_type'] if 'url_type' in row.keys() else 'regular'
                    error_count = row['error_count'] if 'error_count' in row.keys() else 0
                    last_error = row['last_error'] if 'last_error' in row.keys() else None
                    enabled = row['enabled'] if 'enabled' in row.keys() else True
                    added_at = row['added_at'] if 'added_at' in row.keys() else row['last_processed']

                    v2_cursor.execute("""
                        INSERT INTO scraped_urls (
                            url, url_type, status, last_processed, last_scraped,
                            error_count, last_error, error, enabled, added_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['url'],
                        url_type,
                        row['status'],
                        row['last_processed'],
                        row['last_processed'],  # Use last_processed as last_scraped
                        error_count,
                        last_error,
                        last_error,  # Use last_error as error for backward compatibility
                        enabled,
                        added_at
                    ))

                    new_id = v2_cursor.lastrowid
                    self.id_mappings['scraped_urls'][row['id']] = new_id
                    migrated_count += 1

                except Exception as e:
                    print(f"Error migrating scraped URL {row['id']}: {e}")
                    continue

            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} scraped URLs")

        except Exception as e:
            print(f"Error during scraped URLs migration: {e}")
        finally:
            if v1_conn:
                v1_conn.close()
            if v2_conn:
                v2_conn.close()

    def migrate_epg_sources(self):
        """Migrate EPG sources (needed for foreign keys)"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating EPG sources...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='epg_sources';")
            if not v1_cursor.fetchone():
                print("epg_sources table not found in v1 database")
                return

            v1_cursor.execute("SELECT * FROM epg_sources ORDER BY id;")
            v1_sources = v1_cursor.fetchall()

            print(f"Found {len(v1_sources)} EPG sources in v1 database")

            migrated_count = 0
            for row in v1_sources:
                try:
                    # Handle NULL name constraint - use URL as fallback
                    name = row['name'] if row['name'] else f"Source {row['id']}"

                    # Insert and get new ID
                    v2_cursor.execute("""
                        INSERT INTO epg_sources (url, name, enabled, last_updated, error_count, last_error)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['url'],
                        name,
                        row['enabled'],
                        row['last_updated'],
                        row['error_count'],
                        row['last_error']
                    ))

                    new_id = v2_cursor.lastrowid
                    self.id_mappings['epg_sources'][row['id']] = new_id
                    migrated_count += 1

                except Exception as e:
                    print(f"Error migrating EPG source {row['id']}: {e}")
                    continue

            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} EPG sources")

        except Exception as e:
            print(f"Error during EPG sources migration: {e}")
        finally:
            if v1_conn:
                v1_conn.close()
            if v2_conn:
                v2_conn.close()

    def migrate_tv_channels(self):
        """Migrate TV channels with EPG source foreign keys"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating TV channels...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tv_channels';")
            if not v1_cursor.fetchone():
                print("tv_channels table not found in v1 database")
                return

            v1_cursor.execute("SELECT * FROM tv_channels ORDER BY id;")
            v1_channels = v1_cursor.fetchall()

            print(f"Found {len(v1_channels)} TV channels in v1 database")

            migrated_count = 0
            for row in v1_channels:
                try:
                    # Map foreign key
                    epg_source_id = None
                    if row['epg_source_id']:
                        epg_source_id = self.id_mappings['epg_sources'].get(row['epg_source_id'])

                    # Insert and get new ID
                    v2_cursor.execute("""
                        INSERT INTO tv_channels
                        (name, description, logo_url, category, country, language, website,
                         epg_id, epg_source_id, created_at, updated_at, is_active, is_favorite, channel_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['name'],
                        row['description'],
                        row['logo_url'],
                        row['category'],
                        row['country'],
                        row['language'],
                        row['website'],
                        row['epg_id'],
                        epg_source_id,
                        row['created_at'],
                        row['updated_at'],
                        row['is_active'],
                        row['is_favorite'],
                        row['channel_number']
                    ))

                    new_id = v2_cursor.lastrowid
                    self.id_mappings['tv_channels'][row['id']] = new_id
                    migrated_count += 1

                except Exception as e:
                    print(f"Error migrating TV channel {row['id']}: {e}")
                    continue

            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} TV channels")

        except Exception as e:
            print(f"Error during TV channels migration: {e}")
        finally:
            if v1_conn:
                v1_conn.close()
            if v2_conn:
                v2_conn.close()

    def migrate_epg_channels(self):
        """Migrate EPG channels with EPG source foreign keys"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating EPG channels...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='epg_channels';")
            if not v1_cursor.fetchone():
                print("epg_channels table not found in v1 database")
                return

            v1_cursor.execute("SELECT * FROM epg_channels ORDER BY id;")
            v1_epg_channels = v1_cursor.fetchall()

            print(f"Found {len(v1_epg_channels)} EPG channels in v1 database")

            migrated_count = 0
            for row in v1_epg_channels:
                try:
                    # Map foreign key
                    epg_source_id = None
                    if row['epg_source_id']:
                        epg_source_id = self.id_mappings['epg_sources'].get(row['epg_source_id'])
                        if not epg_source_id:
                            print(f"Warning: EPG source {row['epg_source_id']} not found for channel {row['id']}")
                            continue

                    # Insert and get new ID
                    v2_cursor.execute("""
                        INSERT INTO epg_channels
                        (epg_source_id, channel_xml_id, name, icon_url, language, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        epg_source_id,
                        row['channel_xml_id'],
                        row['name'],
                        row['icon_url'],
                        row['language'],
                        row['created_at'],
                        row['updated_at']
                    ))

                    new_id = v2_cursor.lastrowid
                    self.id_mappings['epg_channels'][row['id']] = new_id
                    migrated_count += 1

                except Exception as e:
                    print(f"Error migrating EPG channel {row['id']}: {e}")
                    continue

            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} EPG channels")

        except Exception as e:
            print(f"Error during EPG channels migration: {e}")
        finally:
            if v1_conn:
                v1_conn.close()
            if v2_conn:
                v2_conn.close()

    def migrate_acestream_channels(self):
        """Migrate acestream channels with TV channel foreign keys"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating acestream channels...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='acestream_channels';")
            if not v1_cursor.fetchone():
                print("acestream_channels table not found in v1 database")
                return

            v1_cursor.execute("SELECT * FROM acestream_channels;")
            v1_channels = v1_cursor.fetchall()

            print(f"Found {len(v1_channels)} acestream channels in v1 database")

            migrated_count = 0
            for row in v1_channels:
                try:
                    # Map foreign key
                    tv_channel_id = None
                    if row['tv_channel_id']:
                        tv_channel_id = self.id_mappings['tv_channels'].get(row['tv_channel_id'])

                    # Insert into v2 database - use GUID as primary key
                    v2_cursor.execute("""
                        INSERT OR REPLACE INTO acestream_channels
                        (id, name, "group", logo, tvg_id, tvg_name, source_url,
                         last_seen, is_active, is_online, last_checked, check_error, original_url, epg_update_protected, tv_channel_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['id'],  # v1 uses GUID as primary key
                        row['name'],
                        row['group'],
                        row['logo'],
                        row['tvg_id'],
                        row['tvg_name'],
                        row['source_url'],
                        row['added_at'] or row['last_processed'],
                        row['status'] == 'active' if row['status'] else True,
                        row['is_online'],
                        row['last_checked'],
                        row['check_error'] if 'check_error' in row.keys() else None,  # Handle missing column safely
                        row['original_url'],
                        row['epg_update_protected'] or False,
                        tv_channel_id
                    ))

                    migrated_count += 1

                except Exception as e:
                    print(f"Error migrating acestream channel {row['id']}: {e}")
                    continue

            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} acestream channels")

        except Exception as e:
            print(f"Error during acestream channels migration: {e}")
        finally:
            if v1_conn:
                v1_conn.close()
            if v2_conn:
                v2_conn.close()

    def migrate_epg_string_mappings(self):
        """Migrate EPG string mappings with EPG channel foreign keys"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating EPG string mappings...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='epg_string_mappings';")
            if not v1_cursor.fetchone():
                print("epg_string_mappings table not found in v1 database")
                return

            v1_cursor.execute("SELECT * FROM epg_string_mappings;")
            v1_mappings = v1_cursor.fetchall()

            print(f"Found {len(v1_mappings)} EPG string mappings in v1 database")

            migrated_count = 0
            for row in v1_mappings:
                try:
                    # In v1, epg_channel_id is a string (channel XML ID)
                    # In v2, it's a foreign key to epg_channels.id
                    # We need to find the EPG channel by its channel_xml_id
                    epg_channel_id = None

                    # Find the EPG channel in v2 by its XML ID
                    v2_cursor.execute("""
                        SELECT id FROM epg_channels WHERE channel_xml_id = ?
                    """, (row['epg_channel_id'],))
                    result = v2_cursor.fetchone()

                    if result:
                        epg_channel_id = result[0]
                    else:
                        print(f"Warning: EPG channel {row['epg_channel_id']} not found for mapping {row['id']}")
                        continue

                    # Insert into v2 database
                    v2_cursor.execute("""
                        INSERT INTO epg_string_mappings (epg_channel_id, search_pattern, is_exclusion)
                        VALUES (?, ?, ?)
                    """, (
                        epg_channel_id,
                        row['search_pattern'],
                        row['is_exclusion']
                    ))

                    migrated_count += 1

                except Exception as e:
                    print(f"Error migrating EPG string mapping {row['id']}: {e}")
                    continue

            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} EPG string mappings")

        except Exception as e:
            print(f"Error during EPG string mappings migration: {e}")
        finally:
            if v1_conn:
                v1_conn.close()
            if v2_conn:
                v2_conn.close()

    def migrate_settings(self):
        """Migrate settings from v1 to v2"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating settings...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings';")
            if not v1_cursor.fetchone():
                print("settings table not found in v1 database")
                return

            v1_cursor.execute("SELECT * FROM settings;")
            v1_settings = v1_cursor.fetchall()

            print(f"Found {len(v1_settings)} settings in v1 database")

            migrated_count = 0
            for row in v1_settings:
                try:
                    # V2 uses integer primary key, not string
                    v2_cursor.execute("""
                        INSERT OR REPLACE INTO settings (key, value, description)
                        VALUES (?, ?, ?)
                    """, (
                        row['key'],
                        row['value'],
                        None  # v1 doesn't have description field
                    ))
                    migrated_count += 1
                except Exception as e:
                    print(f"Error migrating setting {row['key']}: {e}")
                    continue

            v2_conn.commit()
            print(f"Successfully migrated {migrated_count} settings")

        except Exception as e:
            print(f"Error during settings migration: {e}")
        finally:
            if v1_conn:
                v1_conn.close()
            if v2_conn:
                v2_conn.close()

    def finalize_migration(self):
        """Rename old database and cleanup"""
        if os.path.exists(self.v1_db_path):
            print(f"Renaming {self.v1_db_path} to {self.v1_migrated_path}")
            try:
                shutil.move(self.v1_db_path, self.v1_migrated_path)
                print("Migration completed and old database archived!")
            except Exception as e:
                print(f"Error renaming database: {e}")

    # ------------------------------------------------------------------
    # Deferred EPG programs migration
    # ------------------------------------------------------------------

    def _count_v1_epg_programs(self) -> int:
        conn = sqlite3.connect(self.v1_db_path)
        try:
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='epg_programs'"
            ).fetchone()
            if not exists:
                return 0
            return int(conn.execute("SELECT COUNT(*) FROM epg_programs").fetchone()[0])
        finally:
            conn.close()

    def load_state(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.state_path):
            return None
        try:
            with open(self.state_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError) as exc:
            print(f"Ignoring unreadable migration state {self.state_path}: {exc}")
            return None

    def _save_state(self, state: Dict[str, Any]) -> None:
        tmp_path = self.state_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
        os.replace(tmp_path, self.state_path)

    def _record_deferred_programs(self, total: int) -> None:
        state = {
            "format": self.STATE_FORMAT,
            "source": self.v1_migrated_path,
            "created_at": _utcnow(),
            "epg_programs": {
                "status": "pending",
                "total": total,
                "migrated": 0,
                "skipped": 0,
                "last_v1_id": 0,
                "epg_channel_ids": {
                    str(old_id): new_id for old_id, new_id in self.id_mappings['epg_channels'].items()
                },
                "started_at": None,
                "finished_at": None,
                "error": None,
                "retryable": True,
            },
        }
        self._save_state(state)

    def deferred_programs_state(self) -> Optional[Dict[str, Any]]:
        state = self.load_state()
        if not state:
            return None
        programs = state.get("epg_programs")
        return programs if isinstance(programs, dict) else None

    def has_deferred_work(self) -> bool:
        """True when EPG programs still need copying (pending, checkpointed, or a retryable error)."""
        programs = self.deferred_programs_state()
        if not programs:
            return False
        status = programs.get("status")
        if status in ("pending", "running"):
            return True
        return status == "error" and bool(programs.get("retryable"))

    @staticmethod
    def _progress_snapshot(programs: Dict[str, Any]) -> Dict[str, Any]:
        total = int(programs.get("total") or 0)
        migrated = int(programs.get("migrated") or 0)
        skipped = int(programs.get("skipped") or 0)
        processed = migrated + skipped
        percent = 100.0 if total == 0 else round(min(processed, total) * 100.0 / total, 1)
        return {
            "status": programs.get("status"),
            "total": total,
            "migrated": migrated,
            "skipped": skipped,
            "processed": processed,
            "percent": percent,
            "last_v1_id": int(programs.get("last_v1_id") or 0),
        }

    def _summary(self, status: str, programs: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = self._progress_snapshot(programs)
        snapshot["status"] = status
        return snapshot

    def run_deferred_migration(
        self,
        progress: Optional[ProgressCallback] = None,
        stop_event: Optional[Event] = None,
    ) -> Dict[str, Any]:
        """Copy the EPG programs recorded by :meth:`run_migration` into v2.

        Safe to call repeatedly: resumes from the checkpoint in the state file
        and never inserts a program that already exists for the same channel,
        start/end time and title. Returns a summary with ``status`` ``done``,
        ``interrupted`` (``stop_event`` was set; call again to resume) or
        ``error`` (permanent failure recorded in the state file).
        """
        state = self.load_state() or {}
        programs = state.get("epg_programs")
        if not isinstance(programs, dict) or programs.get("status") == "done":
            return self._summary("done", programs or {})
        if programs.get("status") == "error" and not programs.get("retryable"):
            return self._summary("error", programs)

        source = state.get("source") or self.v1_migrated_path
        if not os.path.exists(source):
            message = f"Archived v1 database not found at {source}; EPG programs cannot be migrated"
            programs.update(status="error", retryable=False, error=message, finished_at=_utcnow())
            self._save_state(state)
            raise FileNotFoundError(message)

        mapping = {
            int(old_id): int(new_id)
            for old_id, new_id in (programs.get("epg_channel_ids") or {}).items()
        }
        programs["status"] = "running"
        programs["error"] = None
        programs.setdefault("started_at", None)
        if not programs["started_at"]:
            programs["started_at"] = _utcnow()
        self._save_state(state)

        last_id = int(programs.get("last_v1_id") or 0)
        migrated = int(programs.get("migrated") or 0)
        skipped = int(programs.get("skipped") or 0)

        v1_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        v1_conn.row_factory = sqlite3.Row
        v2_conn = sqlite3.connect(self.v2_db_path, timeout=30)
        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    programs.update(status="running", last_v1_id=last_id, migrated=migrated, skipped=skipped)
                    self._save_state(state)
                    return self._summary("interrupted", programs)

                rows = v1_conn.execute(
                    """
                    SELECT id, epg_channel_id, program_xml_id, start_time, end_time, title,
                           subtitle, description, category, icon_url
                    FROM epg_programs
                    WHERE id > ?
                    ORDER BY id
                    LIMIT ?
                    """,
                    (last_id, self.batch_size),
                ).fetchall()
                if not rows:
                    break

                params = []
                for row in rows:
                    channel_id = mapping.get(row["epg_channel_id"]) if row["epg_channel_id"] is not None else None
                    if channel_id is None or not row["start_time"] or not row["end_time"]:
                        # v2 requires a channel and a time range; v1 rows without
                        # them were rejected per-row by the old migrator too.
                        skipped += 1
                        continue
                    title = row["title"] or "Unknown Program"
                    params.append((
                        channel_id,
                        row["program_xml_id"],
                        row["start_time"],
                        row["end_time"],
                        title,
                        row["subtitle"],
                        row["description"],
                        row["category"],
                        row["icon_url"],  # v1 icon_url -> v2 image_url
                        channel_id,
                        row["start_time"],
                        row["end_time"],
                        title,
                    ))

                changes_before = v2_conn.total_changes
                if params:
                    v2_conn.executemany(
                        """
                        INSERT INTO epg_programs
                            (epg_channel_id, program_xml_id, start_time, end_time, title,
                             subtitle, description, category, image_url)
                        SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
                        WHERE NOT EXISTS (
                            SELECT 1 FROM epg_programs
                            WHERE epg_channel_id = ? AND start_time = ? AND end_time = ? AND title = ?
                        )
                        """,
                        params,
                    )
                inserted = v2_conn.total_changes - changes_before
                v2_conn.commit()

                migrated += inserted
                skipped += len(params) - inserted  # already present in v2
                last_id = int(rows[-1]["id"])
                programs.update(last_v1_id=last_id, migrated=migrated, skipped=skipped)
                self._save_state(state)
                if progress is not None:
                    progress(self._progress_snapshot(programs))

            programs.update(status="done", finished_at=_utcnow(), error=None,
                            last_v1_id=last_id, migrated=migrated, skipped=skipped)
            self._save_state(state)
            return self._summary("done", programs)
        except Exception as exc:
            programs.update(status="error", retryable=True, error=str(exc),
                            last_v1_id=last_id, migrated=migrated, skipped=skipped)
            self._save_state(state)
            raise
        finally:
            v1_conn.close()
            v2_conn.close()

    # ------------------------------------------------------------------
    # Foreground migration
    # ------------------------------------------------------------------

    def run_migration(self) -> bool:
        """Run the foreground migration; EPG programs are deferred to the background task."""
        if not self.should_migrate():
            print("No migration needed - either v1 database doesn't exist or already migrated")
            return False

        print("Starting database migration...")
        print(f"V1 database: {self.v1_db_path}")
        print(f"V2 database: {self.v2_db_path}")

        # Provision the v2 schema first so the tables exist even if the v1 file
        # turns out to be unreadable.
        self.create_v2_database()

        # Inspect v1 database
        schemas = self.inspect_v1_database()

        if not schemas:
            print("No v1 database to migrate")
            return False

        # Update v2 schema with any missing columns
        self.update_v2_schema()

        # Migrate the small tables in order (respecting foreign keys)
        self.migrate_scraped_urls()
        self.migrate_epg_sources()
        self.migrate_tv_channels()
        self.migrate_epg_channels()
        self.migrate_acestream_channels()
        self.migrate_epg_string_mappings()
        self.migrate_settings()

        deferred_total = self._count_v1_epg_programs()
        if deferred_total:
            # Record the deferred work BEFORE archiving so a crash in between
            # cannot lose the programs silently.
            self._record_deferred_programs(deferred_total)
            print(
                f"Deferred {deferred_total} EPG programs to background task "
                f"'{self.DEFERRED_TASK_ID}' (state: {self.state_path})"
            )
        elif os.path.exists(self.state_path):
            os.remove(self.state_path)

        # Finalize migration
        self.finalize_migration()

        print("Migration completed successfully!")
        return True


def main():
    """Run both phases synchronously (CLI use)."""
    migrator = DatabaseMigrator()
    migrator.run_migration()
    if migrator.has_deferred_work():
        summary = migrator.run_deferred_migration(progress=lambda p: print(
            f"Migrated {p['processed']}/{p['total']} EPG programs ({p['percent']}%)..."
        ))
        print(f"EPG programs migration finished: {summary}")


if __name__ == "__main__":
    main()

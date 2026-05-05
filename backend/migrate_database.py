"""
Database migration script for Acestream Scraper v1 to v2
"""
import os
import shutil
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.config.database import engine, Base
from app.config.settings import settings
from app.models.models import (
    ScrapedURL,
    AcestreamChannel,
    EPGSource,
    TVChannel,
    EPGChannel,
    EPGProgram,
    EPGStringMapping,
    Setting,
    ActivityLog,  # Ensure new models are imported
    DashboardConfig  # Import new model for dashboard config
)

class DatabaseMigrator:
    def __init__(self):
        self.v1_db_path = settings.LEGACY_DATABASE_URL.replace("sqlite:///", "")
        self.v2_db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        self.v1_migrated_path = self.v1_db_path + ".migrated"

        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.v2_db_path), exist_ok=True)

        # Track ID mappings for foreign keys
        self.id_mappings = {
            'scraped_urls': {},     # old_id -> new_id
            'epg_sources': {},      # old_id -> new_id
            'tv_channels': {},      # old_id -> new_id
            'epg_channels': {},     # old_id -> new_id
        }

    def should_migrate(self) -> bool:
        """Check if migration should run"""
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
        """Create v2 database tables (including new tables like activity_log and dashboard_config)"""
        print("Creating v2 database tables...")
        Base.metadata.create_all(bind=engine)
        print("V2 database tables created successfully!")

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

    def migrate_epg_programs(self):
        """Migrate EPG programs with EPG channel foreign keys"""
        if not os.path.exists(self.v1_db_path):
            return

        print("Migrating EPG programs...")

        v1_conn = None
        v2_conn = None
        try:
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row
            v2_conn = sqlite3.connect(self.v2_db_path)

            v1_cursor = v1_conn.cursor()
            v2_cursor = v2_conn.cursor()

            # Check if table exists
            v1_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='epg_programs';")
            if not v1_cursor.fetchone():
                print("epg_programs table not found in v1 database")
                return

            # Get total count for progress tracking
            v1_cursor.execute("SELECT COUNT(*) FROM epg_programs;")
            total_count = v1_cursor.fetchone()[0]

            print(f"Found {total_count} EPG programs in v1 database")

            # Process in batches to avoid memory issues
            batch_size = 1000
            offset = 0
            migrated_count = 0

            while offset < total_count:
                v1_cursor.execute(f"""
                    SELECT * FROM epg_programs
                    ORDER BY id
                    LIMIT {batch_size} OFFSET {offset}
                """)
                v1_programs = v1_cursor.fetchall()

                if not v1_programs:
                    break

                for row in v1_programs:
                    try:
                        # Map foreign key
                        epg_channel_id = None
                        if row['epg_channel_id']:
                            epg_channel_id = self.id_mappings['epg_channels'].get(row['epg_channel_id'])
                            if not epg_channel_id:
                                # Skip program if channel not found
                                continue

                        # Insert into v2 database
                        v2_cursor.execute("""
                            INSERT INTO epg_programs
                            (epg_channel_id, program_xml_id, start_time, end_time, title,
                             subtitle, description, category, image_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            epg_channel_id,
                            row['program_xml_id'],
                            row['start_time'],
                            row['end_time'],
                            row['title'],
                            row['subtitle'],
                            row['description'],
                            row['category'],
                            row['icon_url']  # v1 uses icon_url, v2 uses image_url
                        ))

                        migrated_count += 1

                    except Exception as e:
                        print(f"Error migrating EPG program {row['id']}: {e}")
                        continue

                # Commit batch and show progress
                v2_conn.commit()
                offset += batch_size
                print(f"Migrated {min(offset, total_count)}/{total_count} EPG programs...")

            print(f"Successfully migrated {migrated_count} EPG programs")

        except Exception as e:
            print(f"Error during EPG programs migration: {e}")
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

    def run_migration(self):
        """Run complete migration process"""
        # Always create v2 database tables (including new tables) before any migration
        self.create_v2_database()

        if not os.path.exists(self.v2_db_path):
            print("No v2 database found, creating a fresh v2 database with all tables...")
            print("Fresh v2 database created!")
            return True

        if not self.should_migrate():
            print("No migration needed - either v1 database doesn't exist or already migrated")
            return False

        print("Starting database migration...")
        print(f"V1 database: {self.v1_db_path}")
        print(f"V2 database: {self.v2_db_path}")

        # Inspect v1 database
        schemas = self.inspect_v1_database()

        if not schemas:
            print("No v1 database to migrate")
            return False

        # Update v2 schema with any missing columns
        self.update_v2_schema()

        # Migrate data in order (respecting foreign keys)
        self.migrate_scraped_urls()
        self.migrate_epg_sources()
        self.migrate_tv_channels()
        self.migrate_epg_channels()
        self.migrate_acestream_channels()
        self.migrate_epg_programs()
        self.migrate_epg_string_mappings()
        self.migrate_settings()

        # Finalize migration
        self.finalize_migration()

        print("Migration completed successfully!")
        return True

def main():
    """Main migration function"""
    migrator = DatabaseMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main()

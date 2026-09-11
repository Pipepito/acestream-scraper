from sqlalchemy import create_engine, inspect, text

from migration_test_utils import database_url_for, downgrade_to_revision, run_alembic, upgraded_inspector, upgrade_to_revision


def _upgraded_tables(db_path) -> set[str]:
    engine, inspector = upgraded_inspector(db_path)
    try:
        return set(inspector.get_table_names())
    finally:
        engine.dispose()


def _assert_core_tables_exist(tables: set[str]) -> None:
    assert 'settings' in tables
    assert 'activity_log' in tables
    assert 'dashboard_config' in tables


def _column_map(inspector, table_name: str) -> dict[str, dict]:
    return {column['name']: column for column in inspector.get_columns(table_name)}


def _prepare_stale_runtime_head_database(db_path) -> None:
    upgrade_to_revision(db_path, 'phase6_add_hotpath_indexes')

    engine = create_engine(database_url_for(db_path))
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    '''
                    CREATE TABLE dashboard_config (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        retention_days INTEGER NOT NULL DEFAULT 7,
                        auto_refresh_interval INTEGER NOT NULL DEFAULT 60
                    )
                    '''
                )
            )

            connection.execute(text('ALTER TABLE settings RENAME TO _settings_stale_head'))
            connection.execute(text('DROP INDEX IF EXISTS ix_settings_key'))
            connection.execute(
                text(
                    '''
                    CREATE TABLE settings (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        key VARCHAR(255) NOT NULL,
                        value VARCHAR(1024),
                        description VARCHAR(1024),
                        CONSTRAINT uq_settings_key UNIQUE (key)
                    )
                    '''
                )
            )
            connection.execute(
                text(
                    '''
                    INSERT INTO settings (key, value, description)
                    SELECT key, value, NULL FROM _settings_stale_head
                    '''
                )
            )
            connection.execute(text('CREATE INDEX ix_settings_key ON settings (key)'))
            connection.execute(text('DROP TABLE _settings_stale_head'))

            connection.execute(text('ALTER TABLE activity_log RENAME TO _activity_log_stale_head'))
            connection.execute(text('DROP INDEX IF EXISTS ix_activity_log_timestamp'))
            connection.execute(text('DROP INDEX IF EXISTS ix_activity_log_type'))
            connection.execute(text('DROP INDEX IF EXISTS ix_activity_log_channel_id'))
            connection.execute(
                text(
                    '''
                    CREATE TABLE activity_log (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        type VARCHAR(32) NOT NULL,
                        message VARCHAR(255) NOT NULL,
                        details TEXT,
                        user VARCHAR(64),
                        channel_id VARCHAR(255),
                        CONSTRAINT fk_activity_log_channel_id FOREIGN KEY(channel_id) REFERENCES acestream_channels (id)
                    )
                    '''
                )
            )
            connection.execute(
                text(
                    '''
                    INSERT INTO activity_log (id, timestamp, type, message, details, user, channel_id)
                    SELECT id, timestamp, type, message, details, user, channel_id
                    FROM _activity_log_stale_head
                    '''
                )
            )
            connection.execute(text('CREATE INDEX ix_activity_log_timestamp ON activity_log (timestamp)'))
            connection.execute(text('CREATE INDEX ix_activity_log_type ON activity_log (type)'))
            connection.execute(text('CREATE INDEX ix_activity_log_channel_id ON activity_log (channel_id)'))
            connection.execute(text('DROP TABLE _activity_log_stale_head'))

            connection.execute(text("UPDATE alembic_version SET version_num = '20260423_1105'"))
    finally:
        engine.dispose()


def _prepare_legacy_integer_id_scraped_urls_database(db_path) -> None:
    upgrade_to_revision(db_path, 't36GeaTCrBqm')

    engine = create_engine(database_url_for(db_path))
    try:
        with engine.begin() as connection:
            connection.execute(text('PRAGMA foreign_keys=OFF'))
            connection.execute(
                text(
                    '''
                    INSERT INTO scraped_urls (url, status, url_type, error_count)
                    VALUES (:url, :status, :url_type, :error_count)
                    '''
                ),
                {
                    'url': 'https://example.com/legacy-integer-id.m3u',
                    'status': 'legacy',
                    'url_type': 'regular',
                    'error_count': 2,
                },
            )
            connection.execute(text('ALTER TABLE scraped_urls ADD COLUMN id INTEGER'))
            connection.execute(text('ALTER TABLE scraped_urls ADD COLUMN temp_guid VARCHAR(36)'))
            connection.execute(
                text(
                    '''
                    UPDATE scraped_urls
                    SET id = rowid
                    WHERE id IS NULL
                    '''
                )
            )
            connection.execute(text('CREATE INDEX ix_scraped_urls_id ON scraped_urls (id)'))
            connection.execute(text('PRAGMA foreign_keys=ON'))
    finally:
        engine.dispose()


def _prepare_preexisting_activity_log_database(db_path) -> None:
    upgrade_to_revision(db_path, '20250412_add_epg_channels_update_tv_channels')

    engine = create_engine(database_url_for(db_path))
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    '''
                    CREATE TABLE dashboard_config (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        retention_days INTEGER NOT NULL DEFAULT 7,
                        auto_refresh_interval INTEGER NOT NULL DEFAULT 60
                    )
                    '''
                )
            )
            connection.execute(
                text(
                    '''
                    INSERT INTO dashboard_config (retention_days, auto_refresh_interval)
                    VALUES (:retention_days, :auto_refresh_interval)
                    '''
                ),
                {'retention_days': 14, 'auto_refresh_interval': 120},
            )

            connection.execute(
                text(
                    '''
                    CREATE TABLE activity_log (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        type VARCHAR(32) NOT NULL,
                        message VARCHAR(255) NOT NULL,
                        details TEXT,
                        user VARCHAR(64),
                        channel_id VARCHAR(255),
                        CONSTRAINT fk_activity_log_channel_id FOREIGN KEY(channel_id) REFERENCES acestream_channels (id)
                    )
                    '''
                )
            )
            connection.execute(text('CREATE INDEX ix_activity_log_timestamp ON activity_log (timestamp)'))
            connection.execute(text('CREATE INDEX ix_activity_log_type ON activity_log (type)'))
            connection.execute(text('CREATE INDEX ix_activity_log_channel_id ON activity_log (channel_id)'))
            connection.execute(
                text(
                    '''
                    INSERT INTO activity_log (type, message, details, user, channel_id)
                    VALUES (:type, :message, :details, :user, :channel_id)
                    '''
                ),
                {
                    'type': 'system',
                    'message': 'preexisting activity log',
                    'details': '{"source": "runtime"}',
                    'user': 'tester',
                    'channel_id': None,
                },
            )
    finally:
        engine.dispose()


def _prepare_partial_activity_log_channel_id_database(db_path) -> None:
    upgrade_to_revision(db_path, 'add_activity_log_table')

    engine = create_engine(database_url_for(db_path))
    try:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE activity_log ADD COLUMN channel_id VARCHAR(255)'))
            connection.execute(
                text(
                    '''
                    INSERT INTO activity_log (type, message, details, user, channel_id)
                    VALUES (:type, :message, :details, :user, :channel_id)
                    '''
                ),
                {
                    'type': 'system',
                    'message': 'partial channel id migration',
                    'details': '{"source": "partial"}',
                    'user': 'tester',
                    'channel_id': None,
                },
            )
    finally:
        engine.dispose()


def test_alembic_upgrade_creates_core_runtime_tables(tmp_path):
    db_path = tmp_path / 'fresh-upgrade.db'

    _assert_core_tables_exist(_upgraded_tables(db_path))


def test_alembic_upgrade_is_repeatable_for_second_fresh_database(tmp_path):
    db_path = tmp_path / 'fresh-upgrade-second.db'

    _assert_core_tables_exist(_upgraded_tables(db_path))


def test_alembic_upgrade_recovers_from_leftover_runtime_align_tables(tmp_path):
    db_path = tmp_path / 'partial-runtime-align.db'
    upgrade_to_revision(db_path, 'phase6_add_hotpath_indexes')

    engine = create_engine(database_url_for(db_path))
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO settings (key, value) VALUES (:key, :value)"
                ),
                {'key': 'base_url', 'value': 'acestream://demo'},
            )
            connection.execute(
                text(
                    "INSERT INTO activity_log (type, message, details, user, channel_id) VALUES (:type, :message, :details, :user, :channel_id)"
                ),
                {
                    'type': 'system',
                    'message': 'runtime alignment',
                    'details': '{"retry": true}',
                    'user': 'tester',
                    'channel_id': None,
                },
            )
            connection.execute(text('ALTER TABLE settings RENAME TO _settings_runtime_align'))
            connection.execute(text('ALTER TABLE activity_log RENAME TO _activity_log_runtime_align'))
    finally:
        engine.dispose()

    result = run_alembic(db_path, 'upgrade', 'head')

    assert result.returncode == 0, result.stderr

    engine = create_engine(database_url_for(db_path))
    inspector = inspect(engine)
    try:
        tables = set(inspector.get_table_names())
        _assert_core_tables_exist(tables)
        assert '_settings_runtime_align' not in tables
        assert '_activity_log_runtime_align' not in tables

        with engine.begin() as connection:
            migrated_setting = connection.execute(
                text("SELECT id, key, value, description FROM settings WHERE key = :key"),
                {'key': 'base_url'},
            ).mappings().one()
            migrated_activity = connection.execute(
                text("SELECT message, details, user FROM activity_log WHERE message = :message"),
                {'message': 'runtime alignment'},
            ).mappings().one()

        assert migrated_setting['id'] is not None
        assert migrated_setting['value'] == 'acestream://demo'
        assert migrated_setting['description'] is None
        assert migrated_activity['details'] == '{"retry": true}'
        assert migrated_activity['user'] == 'tester'
    finally:
        engine.dispose()


def test_alembic_downgrade_recovers_from_leftover_runtime_legacy_tables(tmp_path):
    db_path = tmp_path / 'partial-runtime-legacy.db'
    upgrade_to_revision(db_path, 'head')

    engine = create_engine(database_url_for(db_path))
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO settings (key, value, description) VALUES (:key, :value, :description)"
                ),
                {'key': 'base_url', 'value': 'acestream://demo', 'description': 'demo'},
            )
            connection.execute(
                text(
                    "INSERT INTO activity_log (type, message, details, user, channel_id) VALUES (:type, :message, :details, :user, :channel_id)"
                ),
                {
                    'type': 'system',
                    'message': 'downgrade retry',
                    'details': '{"retry": true}',
                    'user': 'tester',
                    'channel_id': None,
                },
            )
            connection.execute(text('ALTER TABLE settings RENAME TO _settings_runtime_legacy'))
            connection.execute(text('ALTER TABLE activity_log RENAME TO _activity_log_runtime_legacy'))
    finally:
        engine.dispose()


def test_alembic_upgrade_repairs_previously_upgraded_stale_head_database(tmp_path):
    db_path = tmp_path / 'stale-runtime-head.db'
    _prepare_stale_runtime_head_database(db_path)

    engine = create_engine(database_url_for(db_path))
    inspector = inspect(engine)
    try:
        channel_columns = _column_map(inspector, 'acestream_channels')
        scraped_url_columns = _column_map(inspector, 'scraped_urls')

        assert 'last_seen' not in channel_columns
        assert 'last_scraped' not in scraped_url_columns
        assert 'error' not in scraped_url_columns
        assert 'INT' not in str(scraped_url_columns['id']['type']).upper()
    finally:
        engine.dispose()


def test_alembic_upgrade_recovers_from_scraped_urls_with_legacy_integer_id(tmp_path):
    db_path = tmp_path / 'legacy-integer-id.db'
    _prepare_legacy_integer_id_scraped_urls_database(db_path)

    result = run_alembic(db_path, 'upgrade', 'head')

    assert result.returncode == 0, result.stderr

    engine = create_engine(database_url_for(db_path))
    inspector = inspect(engine)
    try:
        scraped_url_columns = _column_map(inspector, 'scraped_urls')
        assert 'INT' in str(scraped_url_columns['id']['type']).upper()

        with engine.begin() as connection:
            migrated_row = connection.execute(
                text(
                    '''
                    SELECT url, status, url_type, error_count
                    FROM scraped_urls
                    WHERE url = :url
                    '''
                ),
                {'url': 'https://example.com/legacy-integer-id.m3u'},
            ).mappings().one()

        assert migrated_row['status'] == 'legacy'
        assert migrated_row['url_type'] == 'regular'
        assert migrated_row['error_count'] == 2
    finally:
        engine.dispose()

    result = run_alembic(db_path, 'upgrade', 'head')

    assert result.returncode == 0, result.stderr

    engine = create_engine(database_url_for(db_path))
    inspector = inspect(engine)
    try:
        channel_columns = _column_map(inspector, 'acestream_channels')
        scraped_url_columns = _column_map(inspector, 'scraped_urls')

        assert 'last_seen' in channel_columns
        assert 'last_scraped' in scraped_url_columns
        assert 'error' in scraped_url_columns
        assert 'INT' in str(scraped_url_columns['id']['type']).upper()
    finally:
        engine.dispose()


def test_alembic_upgrade_recovers_from_preexisting_activity_log_history_gap(tmp_path):
    db_path = tmp_path / 'preexisting-activity-log.db'
    _prepare_preexisting_activity_log_database(db_path)

    result = run_alembic(db_path, 'upgrade', 'head')

    assert result.returncode == 0, result.stderr

    engine = create_engine(database_url_for(db_path))
    inspector = inspect(engine)
    try:
        tables = set(inspector.get_table_names())
        assert 'activity_log' in tables
        assert 'dashboard_config' in tables

        activity_columns = _column_map(inspector, 'activity_log')
        assert 'channel_id' in activity_columns

        with engine.begin() as connection:
            migrated_activity = connection.execute(
                text(
                    '''
                    SELECT message, details, user
                    FROM activity_log
                    WHERE message = :message
                    '''
                ),
                {'message': 'preexisting activity log'},
            ).mappings().one()
            dashboard_config = connection.execute(
                text(
                    '''
                    SELECT retention_days, auto_refresh_interval
                    FROM dashboard_config
                    '''
                )
            ).mappings().one()

        assert migrated_activity['details'] == '{"source": "runtime"}'
        assert migrated_activity['user'] == 'tester'
        assert dashboard_config['retention_days'] == 14
        assert dashboard_config['auto_refresh_interval'] == 120
    finally:
        engine.dispose()


def test_alembic_upgrade_repairs_partial_activity_log_channel_id_migration(tmp_path):
    db_path = tmp_path / 'partial-activity-log-channel-id.db'
    _prepare_partial_activity_log_channel_id_database(db_path)

    result = run_alembic(db_path, 'upgrade', 'head')

    assert result.returncode == 0, result.stderr

    engine = create_engine(database_url_for(db_path))
    inspector = inspect(engine)
    try:
        activity_columns = _column_map(inspector, 'activity_log')
        activity_indexes = {index['name'] for index in inspector.get_indexes('activity_log')}
        activity_foreign_keys = inspector.get_foreign_keys('activity_log')

        assert 'channel_id' in activity_columns
        assert 'ix_activity_log_channel_id' in activity_indexes
        assert any(
            foreign_key.get('constrained_columns') == ['channel_id']
            and foreign_key.get('referred_table') == 'acestream_channels'
            and foreign_key.get('referred_columns') == ['id']
            for foreign_key in activity_foreign_keys
        )

        with engine.begin() as connection:
            migrated_activity = connection.execute(
                text(
                    '''
                    SELECT message, details, user
                    FROM activity_log
                    WHERE message = :message
                    '''
                ),
                {'message': 'partial channel id migration'},
            ).mappings().one()

        assert migrated_activity['details'] == '{"source": "partial"}'
        assert migrated_activity['user'] == 'tester'
    finally:
        engine.dispose()

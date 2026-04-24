from migration_test_utils import upgraded_inspector


def _migrated_inspector(tmp_path, name: str):
    db_path = tmp_path / name
    return upgraded_inspector(db_path)


def _column_map(inspector, table_name: str) -> dict[str, dict]:
    return {column['name']: column for column in inspector.get_columns(table_name)}


def _sqlite_type_name(column: dict) -> str:
    return str(column['type']).upper()


def _has_single_column_index(indexes: list[dict], column_name: str, *, unique: bool | None = None) -> bool:
    for index in indexes:
        if index.get('column_names') != [column_name]:
            continue
        if unique is None or bool(index.get('unique')) is unique:
            return True
    return False


def test_settings_schema_matches_canonical_contract(tmp_path):
    engine, inspector = _migrated_inspector(tmp_path, 'settings-parity.db')
    try:
        columns = _column_map(inspector, 'settings')

        assert set(columns) == {'id', 'key', 'value', 'description'}

        primary_key = inspector.get_pk_constraint('settings')
        assert primary_key['constrained_columns'] == ['id']

        assert columns['key']['nullable'] is False

        unique_constraints = inspector.get_unique_constraints('settings')
        assert any(
            constraint.get('column_names') == ['key'] for constraint in unique_constraints
        )

        indexes = inspector.get_indexes('settings')
        assert any(
            index.get('column_names') == ['key'] for index in indexes
        )

        assert 'last_updated' not in columns
    finally:
        engine.dispose()


def test_activity_log_schema_matches_canonical_contract(tmp_path):
    engine, inspector = _migrated_inspector(tmp_path, 'activity-log-parity.db')
    try:
        columns = _column_map(inspector, 'activity_log')
        details_type = _sqlite_type_name(columns['details'])
        channel_id = columns['channel_id']
        channel_id_type = _sqlite_type_name(channel_id)

        assert 'TEXT' in details_type
        assert 'channel_id' in columns
        assert channel_id['nullable'] is True
        assert 'CHAR' in channel_id_type or 'TEXT' in channel_id_type or 'VARCHAR' in channel_id_type
        assert getattr(channel_id['type'], 'length', None) == 255 or channel_id_type == 'VARCHAR(255)'

        foreign_keys = inspector.get_foreign_keys('activity_log')
        assert any(
            fk.get('constrained_columns') == ['channel_id']
            and fk.get('referred_table') == 'acestream_channels'
            and fk.get('referred_columns') == ['id']
            for fk in foreign_keys
        )
    finally:
        engine.dispose()


def test_dashboard_config_exists_with_canonical_columns(tmp_path):
    engine, inspector = _migrated_inspector(tmp_path, 'dashboard-config-parity.db')
    try:
        tables = set(inspector.get_table_names())
        assert 'dashboard_config' in tables

        columns = _column_map(inspector, 'dashboard_config')
        assert set(columns) == {'id', 'retention_days', 'auto_refresh_interval'}
    finally:
        engine.dispose()


def test_acestream_channels_schema_includes_runtime_last_seen(tmp_path):
    engine, inspector = _migrated_inspector(tmp_path, 'acestream-channels-parity.db')
    try:
        columns = _column_map(inspector, 'acestream_channels')
        assert set(columns) == {
            'id',
            'name',
            'group',
            'logo',
            'tvg_id',
            'tvg_name',
            'source_url',
            'last_seen',
            'is_active',
            'is_online',
            'last_checked',
            'check_error',
            'original_url',
            'epg_update_protected',
            'tv_channel_id',
        }

        channel_id = columns['id']
        channel_id_type = _sqlite_type_name(channel_id)
        last_seen_type = _sqlite_type_name(columns['last_seen'])

        primary_key = inspector.get_pk_constraint('acestream_channels')
        assert primary_key['constrained_columns'] == ['id']
        assert 'CHAR' in channel_id_type or 'TEXT' in channel_id_type or 'VARCHAR' in channel_id_type
        assert getattr(channel_id['type'], 'length', None) == 255 or channel_id_type == 'VARCHAR(255)'
        assert 'DATE' in last_seen_type or 'TIME' in last_seen_type

        indexes = inspector.get_indexes('acestream_channels')
        assert any(index.get('name') == 'ix_acestream_channels_source_active' for index in indexes)
        assert any(index.get('name') == 'ix_acestream_channels_tv_channel_id' for index in indexes)
    finally:
        engine.dispose()


def test_scraped_urls_schema_matches_runtime_contract(tmp_path):
    engine, inspector = _migrated_inspector(tmp_path, 'scraped-urls-parity.db')
    try:
        columns = _column_map(inspector, 'scraped_urls')
        assert set(columns) == {
            'id',
            'url',
            'url_type',
            'status',
            'last_processed',
            'last_scraped',
            'error_count',
            'last_error',
            'error',
            'enabled',
            'added_at',
        }

        primary_key = inspector.get_pk_constraint('scraped_urls')
        assert primary_key['constrained_columns'] == ['id']
        assert 'INT' in _sqlite_type_name(columns['id'])

        assert columns['url']['nullable'] is False
        assert 'DATE' in _sqlite_type_name(columns['last_scraped']) or 'TIME' in _sqlite_type_name(columns['last_scraped'])
        assert 'TEXT' in _sqlite_type_name(columns['error'])

        unique_constraints = inspector.get_unique_constraints('scraped_urls')
        indexes = inspector.get_indexes('scraped_urls')
        assert any(
            constraint.get('column_names') == ['url'] for constraint in unique_constraints
        ) or _has_single_column_index(indexes, 'url', unique=True)
        assert _has_single_column_index(indexes, 'url') or any(
            constraint.get('column_names') == ['url'] for constraint in unique_constraints
        )
    finally:
        engine.dispose()

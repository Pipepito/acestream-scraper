import sys

from sqlalchemy import create_engine, inspect

from app.config.settings import settings


EXPECTED_TABLES = {
    'scraped_urls',
    'settings',
    'dashboard_config',
    'tv_channels',
    'epg_sources',
    'epg_channels',
    'epg_programs',
    'epg_string_mappings',
    'acestream_channels',
    'activity_log',
}

EXPECTED_SETTINGS_COLUMNS = {'id', 'key', 'value', 'description'}
EXPECTED_ACTIVITY_LOG_COLUMNS = {'id', 'timestamp', 'type', 'message', 'details', 'user', 'channel_id'}
EXPECTED_DASHBOARD_CONFIG_COLUMNS = {'id', 'retention_days', 'auto_refresh_interval'}
EXPECTED_ACESTREAM_CHANNEL_COLUMNS = {
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
EXPECTED_SCRAPED_URL_COLUMNS = {
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
    'scrape_bare_ids',
    'added_at',
}


def _column_names(inspector, table_name: str) -> set[str]:
    return {column['name'] for column in inspector.get_columns(table_name)}


def _type_name(inspector, table_name: str, column_name: str) -> str:
    for column in inspector.get_columns(table_name):
        if column['name'] == column_name:
            return str(column['type']).upper()
    return ''


def verify_schema(database_url: str) -> list[str]:
    issues: list[str] = []
    engine = create_engine(database_url)
    inspector = inspect(engine)

    try:
        tables = set(inspector.get_table_names())
        missing_tables = sorted(EXPECTED_TABLES - tables)
        if missing_tables:
            issues.append(f"Missing expected tables: {', '.join(missing_tables)}")

        if 'settings' in tables:
            settings_columns = _column_names(inspector, 'settings')
            if settings_columns != EXPECTED_SETTINGS_COLUMNS:
                issues.append(
                    'settings columns mismatch: '
                    f"expected {sorted(EXPECTED_SETTINGS_COLUMNS)}, got {sorted(settings_columns)}"
                )

        if 'activity_log' in tables:
            activity_columns = _column_names(inspector, 'activity_log')
            if activity_columns != EXPECTED_ACTIVITY_LOG_COLUMNS:
                issues.append(
                    'activity_log columns mismatch: '
                    f"expected {sorted(EXPECTED_ACTIVITY_LOG_COLUMNS)}, got {sorted(activity_columns)}"
                )

        if 'dashboard_config' in tables:
            dashboard_columns = _column_names(inspector, 'dashboard_config')
            if dashboard_columns != EXPECTED_DASHBOARD_CONFIG_COLUMNS:
                issues.append(
                    'dashboard_config columns mismatch: '
                    f"expected {sorted(EXPECTED_DASHBOARD_CONFIG_COLUMNS)}, got {sorted(dashboard_columns)}"
                )

        if 'acestream_channels' in tables:
            channel_columns = _column_names(inspector, 'acestream_channels')
            if channel_columns != EXPECTED_ACESTREAM_CHANNEL_COLUMNS:
                issues.append(
                    'acestream_channels columns mismatch: '
                    f"expected {sorted(EXPECTED_ACESTREAM_CHANNEL_COLUMNS)}, got {sorted(channel_columns)}"
                )

        if 'scraped_urls' in tables:
            scraped_url_columns = _column_names(inspector, 'scraped_urls')
            if scraped_url_columns != EXPECTED_SCRAPED_URL_COLUMNS:
                issues.append(
                    'scraped_urls columns mismatch: '
                    f"expected {sorted(EXPECTED_SCRAPED_URL_COLUMNS)}, got {sorted(scraped_url_columns)}"
                )

            id_type = _type_name(inspector, 'scraped_urls', 'id')
            if 'INT' not in id_type:
                issues.append(f"scraped_urls.id type mismatch: expected integer-compatible type, got {id_type or 'UNKNOWN'}")

        if 'acestream_channels' in tables:
            last_seen_type = _type_name(inspector, 'acestream_channels', 'last_seen')
            if 'DATE' not in last_seen_type and 'TIME' not in last_seen_type:
                issues.append(
                    f"acestream_channels.last_seen type mismatch: expected datetime-compatible type, got {last_seen_type or 'UNKNOWN'}"
                )
    finally:
        engine.dispose()

    return issues


def main() -> int:
    database_url = settings.DATABASE_URL
    issues = verify_schema(database_url)

    print(f"Verifying migrated schema for {database_url}")
    if issues:
        print('FAIL')
        for issue in issues:
            print(f" - {issue}")
        return 1

    print('PASS')
    print(' - expected tables exist')
    print(' - settings matches canonical schema')
    print(' - activity_log matches canonical schema')
    print(' - dashboard_config exists with canonical columns')
    print(' - acestream_channels includes runtime last_seen contract')
    print(' - scraped_urls matches current runtime/API contract')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

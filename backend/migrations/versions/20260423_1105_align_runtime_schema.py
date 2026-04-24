"""Align runtime schema with canonical backend models.

Revision ID: 20260423_1105
Revises: phase6_add_hotpath_indexes
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260423_1105'
down_revision = 'phase6_add_hotpath_indexes'
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _column_names(table_name: str) -> set[str]:
    return {column['name'] for column in _inspector().get_columns(table_name)}


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    indexes = {index['name'] for index in _inspector().get_indexes(table_name)}
    if index_name in indexes:
        op.drop_index(index_name, table_name=table_name)


def _resume_or_create_rebuild_table(source_table: str, temp_table: str, columns) -> bool:
    if _table_exists(source_table):
        if _table_exists(temp_table):
            op.drop_table(temp_table)
        op.create_table(temp_table, *columns)
        return False

    if _table_exists(temp_table):
        op.rename_table(temp_table, source_table)
        op.create_table(temp_table, *columns)
        return False

    return False


def _resume_or_create_legacy_rebuild_table(source_table: str, temp_table: str, columns) -> None:
    if _table_exists(source_table):
        if _table_exists(temp_table):
            op.drop_table(temp_table)
        op.create_table(temp_table, *columns)
        return

    if _table_exists(temp_table):
        op.rename_table(temp_table, source_table)
        op.create_table(temp_table, *columns)


def _create_dashboard_config_if_missing() -> None:
    if _table_exists('dashboard_config'):
        return

    op.create_table(
        'dashboard_config',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('retention_days', sa.Integer(), nullable=False, server_default=sa.text('7')),
        sa.Column('auto_refresh_interval', sa.Integer(), nullable=False, server_default=sa.text('60')),
    )


def _rebuild_activity_log() -> None:
    source_table = 'activity_log'
    temp_table = '_activity_log_runtime_align'
    temp_columns = [
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('message', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('user', sa.String(length=64), nullable=True),
        sa.Column('channel_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['acestream_channels.id'], name='fk_activity_log_channel_id'),
    ]
    _resume_or_create_rebuild_table(source_table, temp_table, temp_columns)
    if not _table_exists(source_table):
        return

    if _table_exists(source_table):
        source_columns = _column_names(source_table)
        channel_id_select = 'channel_id' if 'channel_id' in source_columns else 'NULL AS channel_id'
        op.execute(
            sa.text(
                f'''
                INSERT INTO {temp_table} (id, timestamp, type, message, details, user, channel_id)
                SELECT id, timestamp, type, message, details, user, {channel_id_select}
                FROM {source_table}
                '''
            )
        )

        _drop_index_if_exists('ix_activity_log_timestamp', source_table)
        _drop_index_if_exists('ix_activity_log_type', source_table)
        _drop_index_if_exists('ix_activity_log_channel_id', source_table)
        op.drop_table(source_table)

    op.rename_table(temp_table, 'activity_log')
    op.create_index('ix_activity_log_timestamp', 'activity_log', ['timestamp'])
    op.create_index('ix_activity_log_type', 'activity_log', ['type'])
    op.create_index('ix_activity_log_channel_id', 'activity_log', ['channel_id'])


def _rebuild_settings() -> None:
    source_table = 'settings'
    temp_table = '_settings_runtime_align'
    temp_columns = [
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.String(length=1024), nullable=True),
        sa.Column('description', sa.String(length=1024), nullable=True),
        sa.UniqueConstraint('key', name='uq_settings_key'),
    ]

    if not _table_exists(source_table) and not _table_exists(temp_table):
        op.create_table(
            source_table,
            *temp_columns,
        )
        op.create_index('ix_settings_key', source_table, ['key'])
        return

    _resume_or_create_rebuild_table(source_table, temp_table, temp_columns)
    if _table_exists(source_table):
        source_columns = _column_names(source_table)
        if 'id' in source_columns:
            description_select = 'description' if 'description' in source_columns else 'NULL AS description'
            op.execute(
                sa.text(
                    f'''
                    INSERT INTO {temp_table} (id, key, value, description)
                    SELECT id, key, value, {description_select}
                    FROM {source_table}
                    '''
                )
            )
        else:
            # Legacy settings had no surrogate primary key; allow SQLite to assign ids.
            description_select = 'description' if 'description' in source_columns else 'NULL AS description'
            op.execute(
                sa.text(
                    f'''
                    INSERT INTO {temp_table} (key, value, description)
                    SELECT key, value, {description_select}
                    FROM {source_table}
                    '''
                )
            )

        _drop_index_if_exists('ix_settings_key', source_table)
        op.drop_table(source_table)

    op.rename_table(temp_table, 'settings')
    op.create_index('ix_settings_key', 'settings', ['key'])


def upgrade() -> None:
    _create_dashboard_config_if_missing()
    _rebuild_activity_log()
    _rebuild_settings()


def downgrade() -> None:
    if _table_exists('dashboard_config'):
        op.drop_table('dashboard_config')

    source_table = 'activity_log'
    temp_table = '_activity_log_runtime_legacy'
    temp_columns = [
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('message', sa.String(length=255), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('user', sa.String(length=64), nullable=True),
        sa.Column('channel_id', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['acestream_channels.id'], name='fk_activity_log_channel_id'),
    ]
    _resume_or_create_legacy_rebuild_table(source_table, temp_table, temp_columns)
    if _table_exists(source_table):
        op.execute(
            sa.text(
                f'''
                INSERT INTO {temp_table} (id, timestamp, type, message, details, user, channel_id)
                SELECT id, timestamp, type, message, details, user, channel_id
                FROM {source_table}
                '''
            )
        )
        _drop_index_if_exists('ix_activity_log_timestamp', source_table)
        _drop_index_if_exists('ix_activity_log_type', source_table)
        _drop_index_if_exists('ix_activity_log_channel_id', source_table)
        op.drop_table(source_table)
        op.rename_table(temp_table, 'activity_log')
        op.create_index('ix_activity_log_timestamp', 'activity_log', ['timestamp'])
        op.create_index('ix_activity_log_type', 'activity_log', ['type'])
        op.create_index('ix_activity_log_channel_id', 'activity_log', ['channel_id'])

    source_table = 'settings'
    temp_table = '_settings_runtime_legacy'
    temp_columns = [
        sa.Column('key', sa.String(length=128), nullable=False),
        sa.Column('value', sa.String(length=4096), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('key'),
    ]
    _resume_or_create_legacy_rebuild_table(source_table, temp_table, temp_columns)
    if _table_exists(source_table):
        op.execute(
            sa.text(
                f'''
                INSERT INTO {temp_table} (key, value, last_updated)
                SELECT key, value, NULL
                FROM {source_table}
                '''
            )
        )
        _drop_index_if_exists('ix_settings_key', source_table)
        op.drop_table(source_table)
        op.rename_table(temp_table, 'settings')

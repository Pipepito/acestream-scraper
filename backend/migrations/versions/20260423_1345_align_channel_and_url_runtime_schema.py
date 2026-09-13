"""Align channel and scraped URL runtime schema.

Revision ID: 20260423_1345
Revises: 20260423_1105
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260423_1345'
down_revision = '20260423_1105'
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


def _resume_or_create_rebuild_table(source_table: str, temp_table: str, columns) -> None:
    if _table_exists(source_table):
        if _table_exists(temp_table):
            op.drop_table(temp_table)
        op.create_table(temp_table, *columns)
        return

    if _table_exists(temp_table):
        op.rename_table(temp_table, source_table)
        op.create_table(temp_table, *columns)


def _column_type_name(table_name: str, column_name: str) -> str:
    for column in _inspector().get_columns(table_name):
        if column['name'] == column_name:
            return str(column['type']).upper()
    return ''


def _rebuild_acestream_channels() -> None:
    source_table = 'acestream_channels'
    temp_table = '_acestream_channels_runtime_align'
    temp_columns = [
        sa.Column('id', sa.String(length=255), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('group', sa.String(length=255), nullable=True),
        sa.Column('logo', sa.String(length=2048), nullable=True),
        sa.Column('tvg_id', sa.String(length=255), nullable=True),
        sa.Column('tvg_name', sa.String(length=255), nullable=True),
        sa.Column('source_url', sa.String(length=2048), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('is_online', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('last_checked', sa.DateTime(), nullable=True),
        sa.Column('check_error', sa.Text(), nullable=True),
        sa.Column('original_url', sa.String(length=2048), nullable=True),
        sa.Column('epg_update_protected', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('tv_channel_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['tv_channel_id'], ['tv_channels.id'], name='fk_acestream_channels_tv_channel'),
    ]

    _resume_or_create_rebuild_table(source_table, temp_table, temp_columns)
    if not _table_exists(source_table):
        return

    source_columns = _column_names(source_table)
    last_seen_select = 'last_seen' if 'last_seen' in source_columns else 'last_processed AS last_seen'
    source_url_select = 'source_url' if 'source_url' in source_columns else 'NULL AS source_url'
    original_url_select = 'original_url' if 'original_url' in source_columns else 'NULL AS original_url'
    is_active_select = 'is_active' if 'is_active' in source_columns else '1 AS is_active'
    is_online_select = 'is_online' if 'is_online' in source_columns else 'NULL AS is_online'
    last_checked_select = 'last_checked' if 'last_checked' in source_columns else 'NULL AS last_checked'
    check_error_select = 'check_error' if 'check_error' in source_columns else 'NULL AS check_error'
    epg_update_protected_select = (
        'epg_update_protected' if 'epg_update_protected' in source_columns else '0 AS epg_update_protected'
    )
    tv_channel_id_select = 'tv_channel_id' if 'tv_channel_id' in source_columns else 'NULL AS tv_channel_id'

    op.execute(
        sa.text(
            f'''
            INSERT INTO {temp_table} (
                id,
                name,
                "group",
                logo,
                tvg_id,
                tvg_name,
                source_url,
                last_seen,
                is_active,
                is_online,
                last_checked,
                check_error,
                original_url,
                epg_update_protected,
                tv_channel_id
            )
            SELECT
                id,
                name,
                "group",
                logo,
                tvg_id,
                tvg_name,
                {source_url_select},
                {last_seen_select},
                {is_active_select},
                {is_online_select},
                {last_checked_select},
                {check_error_select},
                {original_url_select},
                {epg_update_protected_select},
                {tv_channel_id_select}
            FROM {source_table}
            '''
        )
    )

    _drop_index_if_exists('ix_acestream_channels_source_active', source_table)
    _drop_index_if_exists('ix_acestream_channels_tv_channel_id', source_table)
    op.drop_table(source_table)
    op.rename_table(temp_table, 'acestream_channels')
    op.create_index('ix_acestream_channels_source_active', 'acestream_channels', ['source_url', 'is_active'])
    op.create_index('ix_acestream_channels_tv_channel_id', 'acestream_channels', ['tv_channel_id'])


def _rebuild_scraped_urls() -> None:
    source_table = 'scraped_urls'
    temp_table = '_scraped_urls_runtime_align'
    temp_columns = [
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('url_type', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=True),
        sa.Column('last_processed', sa.DateTime(), nullable=True),
        sa.Column('last_scraped', sa.DateTime(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('url', name='uq_scraped_urls_url'),
    ]

    _resume_or_create_rebuild_table(source_table, temp_table, temp_columns)
    if not _table_exists(source_table):
        return

    source_columns = _column_names(source_table)
    id_type_name = _column_type_name(source_table, 'id')
    preserve_ids = 'INT' in id_type_name
    last_scraped_select = 'last_scraped' if 'last_scraped' in source_columns else 'last_processed AS last_scraped'
    error_select = 'error' if 'error' in source_columns else 'last_error AS error'
    added_at_select = 'added_at' if 'added_at' in source_columns else 'NULL AS added_at'
    enabled_select = 'enabled' if 'enabled' in source_columns else '1 AS enabled'
    error_count_select = 'error_count' if 'error_count' in source_columns else '0 AS error_count'
    url_type_select = 'url_type' if 'url_type' in source_columns else 'NULL AS url_type'
    status_select = 'status' if 'status' in source_columns else 'NULL AS status'
    last_processed_select = 'last_processed' if 'last_processed' in source_columns else 'NULL AS last_processed'
    last_error_select = 'last_error' if 'last_error' in source_columns else 'NULL AS last_error'

    if preserve_ids:
        op.execute(
            sa.text(
                f'''
                INSERT INTO {temp_table} (
                    id,
                    url,
                    url_type,
                    status,
                    last_processed,
                    last_scraped,
                    error_count,
                    last_error,
                    error,
                    enabled,
                    added_at
                )
                SELECT
                    id,
                    url,
                    {url_type_select},
                    {status_select},
                    {last_processed_select},
                    {last_scraped_select},
                    {error_count_select},
                    {last_error_select},
                    {error_select},
                    {enabled_select},
                    {added_at_select}
                FROM {source_table}
                '''
            )
        )
    else:
        op.execute(
            sa.text(
                f'''
                INSERT INTO {temp_table} (
                    url,
                    url_type,
                    status,
                    last_processed,
                    last_scraped,
                    error_count,
                    last_error,
                    error,
                    enabled,
                    added_at
                )
                SELECT
                    url,
                    {url_type_select},
                    {status_select},
                    {last_processed_select},
                    {last_scraped_select},
                    {error_count_select},
                    {last_error_select},
                    {error_select},
                    {enabled_select},
                    {added_at_select}
                FROM {source_table}
                '''
            )
        )

    _drop_index_if_exists('ix_scraped_urls_enabled_status', source_table)
    _drop_index_if_exists('ix_scraped_urls_url_type_enabled', source_table)
    _drop_index_if_exists('ix_scraped_urls_url', source_table)
    op.drop_table(source_table)
    op.rename_table(temp_table, 'scraped_urls')
    op.create_index('ix_scraped_urls_url', 'scraped_urls', ['url'])
    op.create_index('ix_scraped_urls_enabled_status', 'scraped_urls', ['enabled', 'status'])
    op.create_index('ix_scraped_urls_url_type_enabled', 'scraped_urls', ['url_type', 'enabled'])


def upgrade() -> None:
    _rebuild_acestream_channels()
    _rebuild_scraped_urls()


def downgrade() -> None:
    pass

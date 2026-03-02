"""
Add migration-safe hot-path indexes for phase 6 reliability/performance.
"""
from alembic import op
import sqlalchemy as sa


def _existing_indexes(table_name: str):
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _create_index_if_missing(name: str, table: str, columns):
    if name not in _existing_indexes(table):
        op.create_index(name, table, columns)


def _drop_index_if_exists(name: str, table: str):
    if name in _existing_indexes(table):
        op.drop_index(name, table_name=table)


def upgrade():
    _create_index_if_missing("ix_scraped_urls_enabled_status", "scraped_urls", ["enabled", "status"])
    _create_index_if_missing("ix_scraped_urls_url_type_enabled", "scraped_urls", ["url_type", "enabled"])
    _create_index_if_missing("ix_acestream_channels_source_active", "acestream_channels", ["source_url", "is_active"])
    _create_index_if_missing("ix_acestream_channels_tv_channel_id", "acestream_channels", ["tv_channel_id"])
    _create_index_if_missing("ix_tv_channels_epg_source_epg_id", "tv_channels", ["epg_source_id", "epg_id"])
    _create_index_if_missing("ix_epg_channels_source_xml_id", "epg_channels", ["epg_source_id", "channel_xml_id"])
    _create_index_if_missing("ix_epg_programs_channel_time", "epg_programs", ["epg_channel_id", "start_time", "end_time"])


def downgrade():
    _drop_index_if_exists("ix_epg_programs_channel_time", "epg_programs")
    _drop_index_if_exists("ix_epg_channels_source_xml_id", "epg_channels")
    _drop_index_if_exists("ix_tv_channels_epg_source_epg_id", "tv_channels")
    _drop_index_if_exists("ix_acestream_channels_tv_channel_id", "acestream_channels")
    _drop_index_if_exists("ix_acestream_channels_source_active", "acestream_channels")
    _drop_index_if_exists("ix_scraped_urls_url_type_enabled", "scraped_urls")
    _drop_index_if_exists("ix_scraped_urls_enabled_status", "scraped_urls")

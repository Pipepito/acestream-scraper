"""
Media integrations (spec 6.1, 7.3): remote_players (VLC/Kodi targets) and
media_servers (Jellyfin/Plex sync state). Idempotent for databases that were
provisioned by create_all and stamped afterwards.
"""
from alembic import op
import sqlalchemy as sa


revision = '20260903_1200'
down_revision = '20260824_1200'
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table('remote_players'):
        op.create_table(
            'remote_players',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('name', sa.String(length=255), nullable=False, unique=True),
            sa.Column('kind', sa.String(length=16), nullable=False),
            sa.Column('host', sa.String(length=255), nullable=False),
            sa.Column('port', sa.Integer(), nullable=False, server_default='8080'),
            sa.Column('username', sa.String(length=255), nullable=True),
            sa.Column('password', sa.String(length=1024), nullable=True),
            sa.Column('base_url_id', sa.Integer(), sa.ForeignKey('base_urls.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
    if not _has_table('media_servers'):
        op.create_table(
            'media_servers',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('kind', sa.String(length=16), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False, unique=True),
            sa.Column('base_url', sa.String(length=1024), nullable=False),
            sa.Column('api_key', sa.Text(), nullable=True),
            sa.Column('tuner_mode', sa.String(length=16), nullable=False, server_default='hdhomerun'),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('auto_refresh', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('tuner_host_id', sa.String(length=64), nullable=True),
            sa.Column('listing_provider_id', sa.String(length=64), nullable=True),
            sa.Column('dvr_key', sa.String(length=64), nullable=True),
            sa.Column('last_lineup_fingerprint', sa.String(length=64), nullable=True),
            sa.Column('last_guide_fingerprint', sa.String(length=64), nullable=True),
            sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_sync_status', sa.String(length=16), nullable=False, server_default='never'),
            sa.Column('last_error', sa.Text(), nullable=True),
            sa.Column('server_version', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    if _has_table('media_servers'):
        op.drop_table('media_servers')
    if _has_table('remote_players'):
        op.drop_table('remote_players')

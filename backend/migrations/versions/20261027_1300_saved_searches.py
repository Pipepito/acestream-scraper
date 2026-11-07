"""Saved catalogue definitions and additive memberships; no subscriptions backfilled."""
from alembic import op
import sqlalchemy as sa
revision = '20261027_1300'
down_revision = '20261027_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('saved_searches', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False), sa.Column('query', sa.String(256), nullable=False),
        sa.Column('category', sa.String(100), nullable=False), sa.Column('fingerprint', sa.String(64), nullable=False, unique=True),
        sa.Column('refresh_enabled', sa.Boolean(), nullable=False), sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        *[sa.Column(name, sa.DateTime(timezone=True)) for name in ('last_attempt_at', 'last_started_at', 'last_finished_at', 'last_success_at')],
        sa.Column('last_outcome', sa.String(32)), sa.Column('last_result', sa.JSON()),
        sa.Column('error_code', sa.String(64)), sa.Column('error_message', sa.String(255)),
        sa.Column('run_id', sa.String(32)), sa.Column('run_state', sa.String(32)))
    op.create_table('saved_search_channels',
        sa.Column('saved_search_id', sa.Integer(), sa.ForeignKey('saved_searches.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('channel_id', sa.String(255), sa.ForeignKey('acestream_channels.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('first_discovered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_discovered_at', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table('saved_search_channels')
    op.drop_table('saved_searches')

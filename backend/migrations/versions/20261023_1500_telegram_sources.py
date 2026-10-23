"""Telegram source progress and bounded provenance; never account secrets."""
from alembic import op
import sqlalchemy as sa

revision = '20261023_1500'
down_revision = '20261023_1400'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('telegram_sources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('account_id', sa.String(32), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('chat_label', sa.String(255), nullable=False),
        sa.Column('sender_labels', sa.JSON(), nullable=False),
        sa.Column('cursor', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('last_success', sa.DateTime(timezone=True)),
        sa.Column('imported_count', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(255), nullable=False),
        sa.Column('generation', sa.Integer(), nullable=False))
    op.create_table('telegram_observations',
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('telegram_sources.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('message_id', sa.Integer(), primary_key=True),
        sa.Column('revision', sa.String(64), nullable=False),
        sa.Column('channel_ids', sa.JSON(), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_telegram_observation_time', 'telegram_observations', ['source_id', 'observed_at'])


def downgrade():
    op.drop_table('telegram_observations')
    op.drop_table('telegram_sources')

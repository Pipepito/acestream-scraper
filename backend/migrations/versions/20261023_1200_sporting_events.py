"""Separate sports schedules, provenance and private event-only media."""
from alembic import op
import sqlalchemy as sa

revision = '20261023_1200'
down_revision = '20261021_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sporting_events',
        sa.Column('owner_id', sa.String(32), nullable=False),
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('fields', sa.JSON(), nullable=False),
        sa.Column('correction', sa.JSON(), nullable=True),
        sa.Column('followed', sa.Boolean(), nullable=False),
        sa.Column('archived', sa.Boolean(), nullable=False))
    op.create_table('event_observations',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('event_id', sa.String(32), sa.ForeignKey('sporting_events.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_id', sa.String(160), nullable=False),
        sa.Column('external_id', sa.String(200), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('source_id', 'external_id', name='uq_event_observation_identity'))
    op.create_index('ix_event_observations_event_id', 'event_observations', ['event_id'])
    op.create_table('event_media',
        sa.Column('content_id', sa.String(44), primary_key=True),
        sa.Column('observation_id', sa.String(32), sa.ForeignKey('event_observations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('headers', sa.JSON(), nullable=False))
    op.create_index('ix_event_media_observation_id', 'event_media', ['observation_id'])


def downgrade():
    op.drop_table('event_media')
    op.drop_table('event_observations')
    op.drop_table('sporting_events')

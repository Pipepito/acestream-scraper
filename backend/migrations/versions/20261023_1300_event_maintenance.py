"""Reviewed schedule refresh and conservative archive retention."""
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa

revision = '20261023_1300'
down_revision = '20261023_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sporting_events', sa.Column('broadcast_mappings', sa.JSON(), nullable=True))
    op.add_column('sporting_events', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))
    # Existing archives start their retention clock at upgrade, never in the past.
    events = sa.table('sporting_events', sa.column('archived'), sa.column('archived_at', sa.DateTime(timezone=True)))
    op.execute(events.update().where(events.c.archived.is_(True)).values(archived_at=datetime.now(timezone.utc)))
    op.create_table('event_schedule_sources',
        sa.Column('adapter', sa.JSON(), nullable=True),
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('source_identity', sa.String(160), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('reviewed_ids', sa.JSON(), nullable=False),
        sa.Column('last_attempt', sa.DateTime(timezone=True)),
        sa.Column('last_success', sa.DateTime(timezone=True)),
        sa.Column('last_result', sa.JSON()))


def downgrade():
    op.drop_table('event_schedule_sources')
    with op.batch_alter_table('sporting_events') as batch:
        batch.drop_column('archived_at')
        batch.drop_column('broadcast_mappings')

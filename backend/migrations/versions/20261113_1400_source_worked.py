"""Sources remember when they last worked and how many checks failed since.

Backfill: a source that was online at its last check worked then, and so did
one the relay played (an ``ok`` or ``handover`` attempt). Failures start
counting from here.
"""
from alembic import op
import sqlalchemy as sa

revision = '20261113_1400'
down_revision = '20261109_1300'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.add_column(sa.Column('last_worked_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('failed_checks', sa.Integer(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('failing_since', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE acestream_channels SET last_worked_at = last_checked "
               "WHERE is_online = 1 AND last_checked IS NOT NULL")
    op.execute("""
        UPDATE acestream_channels SET last_worked_at = (
            SELECT max(a.created_at) FROM stream_attempts a
            WHERE lower(a.content_id) = lower(acestream_channels.id) AND a.outcome IN ('ok', 'handover'))
        WHERE EXISTS (
            SELECT 1 FROM stream_attempts a
            WHERE lower(a.content_id) = lower(acestream_channels.id) AND a.outcome IN ('ok', 'handover')
              AND (acestream_channels.last_worked_at IS NULL OR a.created_at > acestream_channels.last_worked_at))
    """)


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('failing_since')
        batch.drop_column('failed_checks')
        batch.drop_column('last_worked_at')

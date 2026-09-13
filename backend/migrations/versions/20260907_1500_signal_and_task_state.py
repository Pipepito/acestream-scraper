"""Separate ID lookup from signal verification and retain scheduler outcomes."""
from alembic import op
import sqlalchemy as sa

revision = '20260907_1500'
down_revision = '20260906_1300'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('acestream_channels', sa.Column('network_status', sa.String(16), nullable=True))
    # Old positives include catalogue imports and P2P counters, not verified media.
    op.execute('UPDATE acestream_channels SET is_online = NULL, last_checked = NULL, check_error = NULL')
    op.create_table('scheduled_task_states',
        sa.Column('task_name', sa.String(128), primary_key=True),
        sa.Column('last_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_result', sa.JSON(), nullable=True))


def downgrade():
    op.drop_table('scheduled_task_states')
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('network_status')

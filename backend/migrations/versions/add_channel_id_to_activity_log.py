"""
Add channel_id to activity_log table
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_channel_id_to_activity_log'
down_revision = 'add_activity_log_table'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('activity_log', recreate='always') as batch_op:
        batch_op.add_column(sa.Column('channel_id', sa.String(64), nullable=True))
        batch_op.create_index('ix_activity_log_channel_id', ['channel_id'])
        batch_op.create_foreign_key(
            'fk_activity_log_channel_id',
            'acestream_channels',
            ['channel_id'],
            ['id'],
        )


def downgrade():
    with op.batch_alter_table('activity_log', recreate='always') as batch_op:
        batch_op.drop_index('ix_activity_log_channel_id')
        batch_op.drop_column('channel_id')

"""
Add channel_id to activity_log table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('activity_log', sa.Column('channel_id', sa.String(255), nullable=True))
    op.create_index('ix_activity_log_channel_id', 'activity_log', ['channel_id'])
    op.create_foreign_key('fk_activity_log_channel_id', 'activity_log', 'acestream_channels', ['channel_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_activity_log_channel_id', 'activity_log', type_='foreignkey')
    op.drop_index('ix_activity_log_channel_id', table_name='activity_log')
    op.drop_column('activity_log', 'channel_id')

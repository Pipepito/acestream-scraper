"""
Alembic migration for activity_log table
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_activity_log_table'
down_revision = '20250412_add_epg_channels_update_tv_channels'
branch_labels = None
depends_on = None


def _table_exists(table_name):
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_names(table_name):
    inspector = sa.inspect(op.get_bind())
    return {column['name'] for column in inspector.get_columns(table_name)}


def _index_names(table_name):
    inspector = sa.inspect(op.get_bind())
    return {index['name'] for index in inspector.get_indexes(table_name)}

def upgrade():
    expected_columns = {'id', 'timestamp', 'type', 'message', 'details', 'user'}
    if _table_exists('activity_log') and expected_columns.issubset(_column_names('activity_log')):
        existing_indexes = _index_names('activity_log')
        if 'ix_activity_log_timestamp' not in existing_indexes:
            op.create_index('ix_activity_log_timestamp', 'activity_log', ['timestamp'])
        if 'ix_activity_log_type' not in existing_indexes:
            op.create_index('ix_activity_log_type', 'activity_log', ['type'])
        return

    op.create_table(
        'activity_log',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True, nullable=False),
        sa.Column('type', sa.String(32), nullable=False, index=True),
        sa.Column('message', sa.String(255), nullable=False),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('user', sa.String(64), nullable=True),
    )

def downgrade():
    op.drop_table('activity_log')

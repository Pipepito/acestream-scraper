"""
Add channel_id to activity_log table
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_channel_id_to_activity_log'
down_revision = 'add_activity_log_table'
branch_labels = None
depends_on = None


def _column_names(table_name):
    inspector = sa.inspect(op.get_bind())
    return {column['name'] for column in inspector.get_columns(table_name)}


def _index_names(table_name):
    inspector = sa.inspect(op.get_bind())
    return {index['name'] for index in inspector.get_indexes(table_name)}


def _foreign_key_names(table_name):
    inspector = sa.inspect(op.get_bind())
    return {foreign_key['name'] for foreign_key in inspector.get_foreign_keys(table_name)}


def _has_channel_id_foreign_key(table_name):
    inspector = sa.inspect(op.get_bind())
    for foreign_key in inspector.get_foreign_keys(table_name):
        if (
            foreign_key.get('constrained_columns') == ['channel_id']
            and foreign_key.get('referred_table') == 'acestream_channels'
            and foreign_key.get('referred_columns') == ['id']
        ):
            return True
    return False


def upgrade():
    existing_columns = _column_names('activity_log')
    existing_indexes = _index_names('activity_log')
    has_channel_id_fk = _has_channel_id_foreign_key('activity_log')

    if 'channel_id' in existing_columns and 'ix_activity_log_channel_id' in existing_indexes and has_channel_id_fk:
        return

    if 'channel_id' in existing_columns:
        with op.batch_alter_table('activity_log', recreate='always') as batch_op:
            if 'ix_activity_log_channel_id' not in existing_indexes:
                batch_op.create_index('ix_activity_log_channel_id', ['channel_id'])
            if not has_channel_id_fk:
                batch_op.create_foreign_key(
                    'fk_activity_log_channel_id',
                    'acestream_channels',
                    ['channel_id'],
                    ['id'],
                )
        return

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

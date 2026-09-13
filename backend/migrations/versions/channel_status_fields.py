"""Add channel status fields

Revision ID: channel_status_fields_02
Revises: fb06651a94c1
Create Date: 2024-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'channel_status_fields_02'
down_revision = 'fb06651a94c1'
branch_labels = None
depends_on = None


def has_column(table, column):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    columns = [c["name"] for c in insp.get_columns(table)]
    return column in columns


def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('acestream_channels') as batch_op:
        # Add columns only if they don't exist
        if not has_column('acestream_channels', 'is_active'):
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'))
        if not has_column('acestream_channels', 'is_online'):
            batch_op.add_column(sa.Column('is_online', sa.Boolean(), nullable=True, server_default='0'))
        if not has_column('acestream_channels', 'last_checked'):
            batch_op.add_column(sa.Column('last_checked', sa.DateTime(), nullable=True))
        if not has_column('acestream_channels', 'check_error'):
            batch_op.add_column(sa.Column('check_error', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch_op:
        # Only try to drop if columns exist
        if has_column('acestream_channels', 'is_active'):
            batch_op.drop_column('is_active')
        if has_column('acestream_channels', 'is_online'):
            batch_op.drop_column('is_online')
        if has_column('acestream_channels', 'last_checked'):
            batch_op.drop_column('last_checked')
        if has_column('acestream_channels', 'check_error'):
            batch_op.drop_column('check_error')

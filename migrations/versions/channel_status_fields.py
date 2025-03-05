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

def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('acestream_channels') as batch_op:
        batch_op.add_column(sa.Column('is_online', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('last_checked', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('check_error', sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table('acestream_channels') as batch_op:
        batch_op.drop_column('check_error')
        batch_op.drop_column('last_checked')
        batch_op.drop_column('is_online')
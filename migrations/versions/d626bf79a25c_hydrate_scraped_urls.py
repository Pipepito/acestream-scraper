"""Add channel status fields

Revision ID: d626bf79a25c
Revises: 4e3b1a9c8f21
Create Date: 2024-02-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd626bf79a25c' 
down_revision = '4e3b1a9c8f21'
branch_labels = None
depends_on = None

def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('scraped_urls') as batch_op:
        batch_op.add_column(sa.Column('enabled', sa.Boolean(), nullable=True, server_default='1'))
        batch_op.add_column(sa.Column('added_at', sa.DateTime(), nullable=True))

def downgrade():
    with op.batch_alter_table('scraped_urls') as batch_op:
        batch_op.drop_column('enabled')
        batch_op.drop_column('added_at')
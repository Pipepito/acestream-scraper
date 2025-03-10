"""Add channel status fields

Revision ID: h6s6bgh82cxa
Revises: d626bf79a25c
Create Date: 2024-02-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'h6s6bgh82cxa' 
down_revision = 'd626bf79a25c'
branch_labels = None
depends_on = None

def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('settings') as batch_op:
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(), nullable=True))

def downgrade():
    with op.batch_alter_table('settings') as batch_op:
        batch_op.drop_column('last_updated')
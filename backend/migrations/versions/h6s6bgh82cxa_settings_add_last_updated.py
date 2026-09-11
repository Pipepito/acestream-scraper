"""Add last_updated field to settings

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


def has_column(table, column):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    columns = [c["name"] for c in insp.get_columns(table)]
    return column in columns


def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('settings') as batch_op:
        if not has_column('settings', 'last_updated'):
            batch_op.add_column(sa.Column('last_updated', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('settings') as batch_op:
        if has_column('settings', 'last_updated'):
            batch_op.drop_column('last_updated')

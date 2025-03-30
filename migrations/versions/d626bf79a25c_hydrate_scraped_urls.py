"""Hydrate scraped urls

Revision ID: d626bf79a25c
Revises: 4e3b1a9c8f21
Create Date: 2023-11-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'd626bf79a25c'
down_revision = '4e3b1a9c8f21'
branch_labels = None
depends_on = None

def has_column(table, column):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table)]
    return column in columns

def upgrade():
    # Check if columns exist before adding them to avoid duplicate column errors
    with op.batch_alter_table('scraped_urls') as batch_op:
        # Only add enabled column if it doesn't exist
        if not has_column('scraped_urls', 'enabled'):
            batch_op.add_column(sa.Column('enabled', sa.Boolean(), default=True))
        
        # Only add url_type column if it doesn't exist
        if not has_column('scraped_urls', 'url_type'):
            batch_op.add_column(sa.Column('url_type', sa.String(length=16), default='regular'))
        
        # Only add error_count column if it doesn't exist
        if not has_column('scraped_urls', 'error_count'):
            batch_op.add_column(sa.Column('error_count', sa.Integer(), default=0))
        
        # Only add last_error column if it doesn't exist
        if not has_column('scraped_urls', 'last_error'):
            batch_op.add_column(sa.Column('last_error', sa.Text(), nullable=True))

def downgrade():
    # Since we're checking for column existence in upgrade,
    # we should do the same for downgrade to make it idempotent
    with op.batch_alter_table('scraped_urls') as batch_op:
        if has_column('scraped_urls', 'enabled'):
            batch_op.drop_column('enabled')
        if has_column('scraped_urls', 'url_type'):
            batch_op.drop_column('url_type')
        if has_column('scraped_urls', 'error_count'):
            batch_op.drop_column('error_count')
        if has_column('scraped_urls', 'last_error'):
            batch_op.drop_column('last_error')
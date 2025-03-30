"""add added_at to scraped urls

Revision ID: 20250330_add_added_at
Revises: YtQg2uH3sL7m
Create Date: 2025-03-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20250330_add_added_at'
down_revision = 'YtQg2uH3sL7m'
branch_labels = None
depends_on = None

def has_column(table, column):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table)]
    return column in columns

def upgrade():
    # Check if the column already exists to avoid errors
    if not has_column('scraped_urls', 'added_at'):
        # Use batch_alter_table for SQLite compatibility
        with op.batch_alter_table('scraped_urls') as batch_op:
            batch_op.add_column(sa.Column('added_at', sa.DateTime(), 
                                          nullable=True, 
                                          server_default=sa.func.current_timestamp()))
        
        # Set default value for existing rows
        conn = op.get_bind()
        conn.execute(sa.text("UPDATE scraped_urls SET added_at = CURRENT_TIMESTAMP WHERE added_at IS NULL"))

def downgrade():
    # Only try to drop the column if it exists
    if has_column('scraped_urls', 'added_at'):
        with op.batch_alter_table('scraped_urls') as batch_op:
            batch_op.drop_column('added_at')

"""Initial migration

Revision ID: fb06651a94c1
"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb06651a94c1'
down_revision = None
branch_labels = None
depends_on = None


def has_table(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return table_name in insp.get_table_names()


def has_column(table, column):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    columns = [c["name"] for c in insp.get_columns(table)]
    return column in columns


def upgrade():
    # Create scraped_urls table
    if not has_table('scraped_urls'):
        op.create_table(
            'scraped_urls',
            sa.Column('url', sa.Text(), nullable=False),
            sa.Column('status', sa.String(32), nullable=True),
            sa.Column('last_processed', sa.DateTime(), nullable=True),
            sa.Column('error_count', sa.Integer(), nullable=True, default=0),
            sa.Column('last_error', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('url')
        )

    # Create acestream_channels table
    if not has_table('acestream_channels'):
        op.create_table(
            'acestream_channels',
            sa.Column('id', sa.String(64), nullable=False),
            sa.Column('name', sa.String(256), nullable=True),
            sa.Column('added_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
            sa.Column('last_processed', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(32), nullable=True, default='active'),
            sa.Column('source_url', sa.Text(), nullable=True),
            sa.Column('group', sa.String(256), nullable=True),
            sa.Column('logo', sa.Text(), nullable=True),
            sa.Column('tvg_id', sa.String(256), nullable=True),
            sa.Column('tvg_name', sa.String(256), nullable=True),
            sa.Column('m3u_source', sa.Text(), nullable=True),
            sa.Column('original_url', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['source_url'], ['scraped_urls.url']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    # Only drop if tables exist
    if has_table('acestream_channels'):
        op.drop_table('acestream_channels')
    if has_table('scraped_urls'):
        op.drop_table('scraped_urls')

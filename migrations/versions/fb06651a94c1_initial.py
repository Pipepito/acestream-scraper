"""Initial migration

Revision ID: fb06651a94c1
Revises: 
Create Date: 2024-02-27

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'fb06651a94c1'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create scraped_urls table
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
    op.drop_table('acestream_channels')
    op.drop_table('scraped_urls')
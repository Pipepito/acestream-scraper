"""add tv channels

Revision ID: 20250409_add_tv_channels
Revises: 20250409_add_missing_fields_to_epg_sources_tables
Create Date: 2025-04-09 22:30:21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic
revision = '20250409_add_tv_channels'
down_revision = '20250409_add_missing_fields_to_epg_sources_tables'
branch_labels = None
depends_on = None

def has_table(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    insp = inspect(conn)
    return table_name in insp.get_table_names()

def has_column(table, column):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    insp = inspect(conn)
    columns = [col['name'] for col in insp.get_columns(table)]
    return column in columns

def upgrade():
    # Create tv_channels table if it doesn't exist
    if not has_table('tv_channels'):
        op.create_table(
            'tv_channels',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=256), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('logo_url', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=128), nullable=True),
            sa.Column('country', sa.String(length=128), nullable=True),
            sa.Column('language', sa.String(length=128), nullable=True),
            sa.Column('website', sa.Text(), nullable=True),
            sa.Column('epg_id', sa.String(length=256), nullable=True),
            sa.Column('epg_source_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.ForeignKeyConstraint(['epg_source_id'], ['epg_sources.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Add tv_channel_id column to acestream_channels table if it doesn't exist
    if has_table('acestream_channels') and not has_column('acestream_channels', 'tv_channel_id'):
        with op.batch_alter_table('acestream_channels', recreate='always') as batch_op:
            # Add the column
            batch_op.add_column(sa.Column('tv_channel_id', sa.Integer(), nullable=True))
            # Create foreign key constraint within the batch operation
            batch_op.create_foreign_key(
                'fk_acestream_channels_tv_channel', 
                'tv_channels', 
                ['tv_channel_id'], 
                ['id']
            )

def downgrade():
    # Use batch_alter_table to handle the constraint drop in SQLite
    if has_table('acestream_channels') and has_column('acestream_channels', 'tv_channel_id'):
        with op.batch_alter_table('acestream_channels', recreate='always') as batch_op:
            # Drop foreign key constraint implicitly by recreating the table
            # Drop tv_channel_id column
            batch_op.drop_column('tv_channel_id')
    
    # Drop tv_channels table if it exists
    if has_table('tv_channels'):
        op.drop_table('tv_channels')

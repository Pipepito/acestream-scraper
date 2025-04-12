"""add epg channels and update tv channels

Revision ID: 20250412_add_epg_channels_update_tv_channels
Revises: 20250409_add_tv_channels
Create Date: 2025-04-12 23:55:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic
revision = '20250412_add_epg_channels_update_tv_channels'
down_revision = '20250409_add_tv_channels'
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
    columns = [c["name"] for c in insp.get_columns(table)]
    return column in columns

def upgrade():
    # 1. Add new columns to tv_channels table
    if has_table('tv_channels'):
        with op.batch_alter_table('tv_channels') as batch_op:
            # Add is_favorite column if it doesn't exist
            if not has_column('tv_channels', 'is_favorite'):
                batch_op.add_column(sa.Column('is_favorite', sa.Boolean(), 
                                             nullable=False, 
                                             server_default=sa.text('0')))
            
            # Add channel_number column if it doesn't exist
            if not has_column('tv_channels', 'channel_number'):
                batch_op.add_column(sa.Column('channel_number', sa.Integer(), 
                                             nullable=True))

    # 2. Create epg_channels table if it doesn't exist
    if not has_table('epg_channels'):
        op.create_table(
            'epg_channels',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('epg_source_id', sa.Integer(), nullable=False),
            sa.Column('channel_xml_id', sa.String(255), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('icon_url', sa.Text(), nullable=True),
            sa.Column('language', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), 
                     server_default=sa.text('CURRENT_TIMESTAMP'),
                     onupdate=sa.text('CURRENT_TIMESTAMP'), 
                     nullable=False),
            sa.ForeignKeyConstraint(['epg_source_id'], ['epg_sources.id']),
            sa.UniqueConstraint('epg_source_id', 'channel_xml_id', name='_epg_source_channel_uc')
        )


def downgrade():
    # 1. Remove columns from tv_channels table
    if has_table('tv_channels'):
        with op.batch_alter_table('tv_channels') as batch_op:
            # Drop is_favorite column if it exists
            if has_column('tv_channels', 'is_favorite'):
                batch_op.drop_column('is_favorite')
            
            # Drop channel_number column if it exists
            if has_column('tv_channels', 'channel_number'):
                batch_op.drop_column('channel_number')
    
    # 2. Drop epg_channels table if it exists
    if has_table('epg_channels'):
        op.drop_table('epg_channels')

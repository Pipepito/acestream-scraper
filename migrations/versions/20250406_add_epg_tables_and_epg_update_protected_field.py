"""20250406_add_epg_update_protected

Revision ID: 20250406_add_epg_update_protected
Revises: 20250330_add_added_at
Create Date: 2025-04-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250406_add_epg_tables_and_epg_update_protected_field'
down_revision = '20250330_add_added_at_to_scraped_urls'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands to upgrade database ###
    
    # Add epg_update_protected column to acestream_channels table
    op.add_column('acestream_channels', 
                  sa.Column('epg_update_protected', sa.Boolean(), 
                            server_default=sa.text('FALSE'), 
                            nullable=False))
    
    # Create epg_sources table
    op.create_table(
        'epg_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('error_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), 
                  onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # Create index for URL uniqueness
    op.create_index(op.f('ix_epg_sources_url'), 'epg_sources', ['url'], unique=True)
    
    # Create epg_string_mappings table
    op.create_table(
        'epg_string_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('search_pattern', sa.String(), nullable=False),
        sa.Column('epg_channel_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), 
                  onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # Create index for search pattern uniqueness
    op.create_index(op.f('ix_epg_string_mappings_search_pattern'), 'epg_string_mappings', ['search_pattern'], unique=True)
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands to downgrade database ###
    
    # Drop the tables we created
    op.drop_index(op.f('ix_epg_string_mappings_search_pattern'), table_name='epg_string_mappings')
    op.drop_table('epg_string_mappings')
    
    op.drop_index(op.f('ix_epg_sources_url'), table_name='epg_sources')
    op.drop_table('epg_sources')
    
    # Drop epg_update_protected column from acestream_channels table
    op.drop_column('acestream_channels', 'epg_update_protected')
    # ### end Alembic commands ###

"""20250409_add_missing_fields_to_epg_sources_tables

Revision ID: 20250409_add_missing_fields_to_epg_sources_tables
Revises: 20250406_add_epg_tables_and_epg_update_protected_field
Create Date: 2025-05-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20250409_add_missing_fields_to_epg_sources_tables'
down_revision = '20250406_add_epg_tables_and_epg_update_protected_field'
branch_labels = None
depends_on = None


def column_exists(table, column):
    """Check if a column exists in a table."""
    conn = op.get_bind()
    insp = inspect(conn)
    columns = [col['name'] for col in insp.get_columns(table)]
    return column in columns


def upgrade():
    # ### commands to upgrade database ###
    if not column_exists('epg_sources', 'name'):
        op.add_column('epg_sources', 
                     sa.Column('name', sa.String(), nullable=True))         

    if not column_exists('epg_sources', 'last_error'):
        op.add_column('epg_sources', 
                     sa.Column('last_error', sa.String(), nullable=True))

    if not column_exists('epg_string_mappings', 'last_error'):
        op.add_column('epg_string_mappings', 
                     sa.Column('is_exclusion', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands to downgrade database ###
    if column_exists('epg_sources', 'name'):
        op.drop_column('epg_sources', 'name')

    if column_exists('epg_sources', 'last_error'):
        op.drop_column('epg_sources', 'last_error')
        
    if column_exists('epg_string_mappings', 'is_exclusion'):
        op.drop_column('epg_string_mappings', 'is_exclusion')
    # ### end Alembic commands ###

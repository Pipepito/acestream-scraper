"""Preserve XMLTV categories and ownership of stable channel classifications."""
from alembic import op
import sqlalchemy as sa

revision = '20261109_1300'
down_revision = '20261109_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tv_channels', sa.Column('category_origin', sa.String(32), nullable=False, server_default='legacy'))
    op.add_column('tv_channels', sa.Column('category_revision', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tv_channels', sa.Column('category_evidence', sa.JSON(), nullable=True))
    op.create_table('epg_program_categories',
                    sa.Column('program_id', sa.Integer(), sa.ForeignKey('epg_programs.id', ondelete='CASCADE'), primary_key=True),
                    sa.Column('position', sa.Integer(), primary_key=True),
                    sa.Column('label', sa.String(1024), nullable=False),
                    sa.Column('language', sa.String(50), nullable=True))
    op.create_index('ix_epg_program_categories_label', 'epg_program_categories', ['label'])
    op.execute('INSERT INTO epg_program_categories (program_id, position, label) '
               'SELECT id, 0, category FROM epg_programs WHERE category IS NOT NULL')


def downgrade():
    op.drop_table('epg_program_categories')
    op.drop_column('tv_channels', 'category_evidence')
    op.drop_column('tv_channels', 'category_revision')
    op.drop_column('tv_channels', 'category_origin')

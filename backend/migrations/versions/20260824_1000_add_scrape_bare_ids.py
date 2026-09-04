"""
Add scraped_urls.scrape_bare_ids: opt-in harvesting of bare 40-hex content
IDs from sites that list hashes without the acestream:// scheme (#81).
"""
from alembic import op
import sqlalchemy as sa


revision = '20260824_1000'
down_revision = '20260504_1200'
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column['name'] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column('scraped_urls', 'scrape_bare_ids'):
        op.add_column(
            'scraped_urls',
            sa.Column('scrape_bare_ids', sa.Boolean(), nullable=True, server_default=sa.false()),
        )


def downgrade() -> None:
    if _has_column('scraped_urls', 'scrape_bare_ids'):
        op.drop_column('scraped_urls', 'scrape_bare_ids')

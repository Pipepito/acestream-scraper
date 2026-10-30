"""Optional friendly names for scraper sources."""
from alembic import op
import sqlalchemy as sa

revision = '20261030_1200'
down_revision = '20261028_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scraped_urls', sa.Column('name', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('scraped_urls', 'name')

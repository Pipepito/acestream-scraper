"""Persist opt-in extraction recipes without changing existing source behavior."""
from alembic import op
import sqlalchemy as sa

revision = '20260914_1200'
down_revision = '20260907_1500'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scraped_urls', sa.Column('extraction_recipe', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('scraped_urls') as batch:
        batch.drop_column('extraction_recipe')

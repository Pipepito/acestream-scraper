"""Reviewed, reversible event overlays; original guide rows stay intact."""
from alembic import op
import sqlalchemy as sa

revision = '20261030_1300'
down_revision = '20261030_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sporting_events', sa.Column('guide_overlays', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('sporting_events') as batch:
        batch.drop_column('guide_overlays')

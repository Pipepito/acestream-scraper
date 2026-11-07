"""Track observed offline streaks without guessing historical status."""
from alembic import op
import sqlalchemy as sa

revision = '20261107_1200'
down_revision = '20261102_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('acestream_channels', sa.Column('offline_since', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('acestream_channels', 'offline_since')

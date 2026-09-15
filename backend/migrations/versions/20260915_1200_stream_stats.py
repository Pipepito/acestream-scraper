"""Store the latest peer and transfer-rate observation for each stream."""
from alembic import op
import sqlalchemy as sa

revision = '20260915_1200'
down_revision = '20260914_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('acestream_channels', sa.Column('stream_stats', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('stream_stats')

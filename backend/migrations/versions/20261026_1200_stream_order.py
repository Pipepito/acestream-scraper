"""Add stream_order to acestream_channels for channel stream preference."""
from alembic import op
import sqlalchemy as sa

revision = '20261026_1200'
down_revision = '20260928_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('acestream_channels', sa.Column('stream_order', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('stream_order')

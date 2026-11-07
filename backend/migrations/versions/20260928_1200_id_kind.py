"""Remember whether a channel id is an acestream content id or an infohash."""
from alembic import op
import sqlalchemy as sa

revision = '20260928_1200'
down_revision = '20260915_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('acestream_channels', sa.Column('id_kind', sa.String(16), nullable=True))


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('id_kind')

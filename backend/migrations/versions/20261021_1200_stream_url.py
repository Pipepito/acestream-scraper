"""Keep plain HTTP/HLS streams: their URL and the headers their playlist publishes."""
from alembic import op
import sqlalchemy as sa

revision = '20261021_1200'
down_revision = '20260928_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('acestream_channels', sa.Column('stream_url', sa.String(2048), nullable=True))
    op.add_column('acestream_channels', sa.Column('stream_headers', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('stream_headers')
        batch.drop_column('stream_url')

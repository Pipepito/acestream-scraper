"""Per-attempt playback outcomes the tuner ranks sources with."""
from alembic import op
import sqlalchemy as sa

revision = '20261102_1200'
down_revision = '20261103_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('stream_attempts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('content_id', sa.String(255), nullable=False),
        sa.Column('tv_channel_id', sa.Integer()),
        sa.Column('outcome', sa.String(24), nullable=False),
        sa.Column('seconds', sa.Float(), nullable=False),
        sa.Column('peers', sa.Integer()), sa.Column('speed_down', sa.Integer()),
        sa.Column('source_url', sa.String(2048)), sa.Column('channel_sources', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_stream_attempts_content_created', 'stream_attempts', ['content_id', 'created_at'])
    op.create_index('ix_stream_attempts_created', 'stream_attempts', ['created_at'])


def downgrade():
    op.drop_index('ix_stream_attempts_created', table_name='stream_attempts')
    op.drop_index('ix_stream_attempts_content_created', table_name='stream_attempts')
    op.drop_table('stream_attempts')

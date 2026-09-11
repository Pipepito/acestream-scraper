"""Store measured stream bitrate for tuner source selection."""
from alembic import op
import sqlalchemy as sa

revision = '20260906_1300'
down_revision = '20260903_1200'
branch_labels = None
depends_on = None


def upgrade():
    existing = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('acestream_channels')}
    if 'audio_tracks' not in existing:
        op.add_column('acestream_channels', sa.Column('audio_tracks', sa.JSON(), nullable=True))
    if 'bitrate_bps' not in existing:
        op.add_column('acestream_channels', sa.Column('bitrate_bps', sa.Integer(), nullable=True))
    if 'bitrate_checked_at' not in existing:
        op.add_column('acestream_channels', sa.Column('bitrate_checked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('audio_tracks')
        batch.drop_column('bitrate_checked_at')
        batch.drop_column('bitrate_bps')

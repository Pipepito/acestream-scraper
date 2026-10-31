"""Independent recording identities and durable DVR executions."""
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision = '20261028_1200'
down_revision = '20261027_1300'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('epg_sources', sa.Column('recording_uuid', sa.String(32)))
    connection = op.get_bind()
    for sid in connection.execute(sa.text('SELECT id FROM epg_sources')).scalars():
        connection.execute(sa.text('UPDATE epg_sources SET recording_uuid=:value WHERE id=:id'),
                           {'value': uuid4().hex, 'id': sid})
    with op.batch_alter_table('epg_sources') as batch:
        batch.alter_column('recording_uuid', existing_type=sa.String(32), nullable=False, server_default=sa.text('(lower(hex(randomblob(16))))'))
        batch.create_unique_constraint('uq_epg_sources_recording_uuid', ['recording_uuid'])
    op.create_table('recordings',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('tv_channel_id', sa.Integer(), sa.ForeignKey('tv_channels.id', ondelete='SET NULL')),
        sa.Column('occurrence_key', sa.String(64)), sa.Column('snapshot', sa.JSON(), nullable=False),
        *[sa.Column(n, sa.DateTime(timezone=True), nullable=False) for n in ('start_time', 'end_time')],
        sa.Column('timezone', sa.String(64), nullable=False), sa.Column('state', sa.String(24), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('stop_requested', sa.Boolean(), nullable=False), sa.Column('protected', sa.Boolean(), nullable=False),
        sa.Column('actual_start', sa.DateTime(timezone=True)), sa.Column('actual_end', sa.DateTime(timezone=True)),
        sa.Column('reason', sa.String(64)), sa.Column('gaps', sa.JSON(), nullable=False),
        sa.Column('idempotency_key', sa.String(64), nullable=False, unique=True),
        sa.Column('request_hash', sa.String(64), nullable=False),
        *[sa.Column(n, sa.DateTime(timezone=True), nullable=False) for n in ('created_at', 'updated_at')],
        sa.CheckConstraint('end_time > start_time', name='recording_interval'))
    op.create_index('ix_recordings_due', 'recordings', ['state', 'start_time'])
    op.create_index('ix_recordings_occurrence_key', 'recordings', ['occurrence_key'])
    op.create_table('recording_attempts',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('recording_id', sa.String(32), sa.ForeignKey('recordings.id'), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=False), sa.Column('source_id', sa.String(255), nullable=False),
        sa.Column('route', sa.String(16), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True)), sa.Column('exit_code', sa.Integer()),
        sa.Column('reason', sa.String(64)), sa.Column('process_identity', sa.JSON()),
        sa.UniqueConstraint('recording_id', 'ordinal'))
    op.create_index('ix_recording_attempts_recording_id', 'recording_attempts', ['recording_id'])
    op.create_table('recording_artifacts',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('recording_id', sa.String(32), sa.ForeignKey('recordings.id'), nullable=False),
        sa.Column('attempt_id', sa.String(32), sa.ForeignKey('recording_attempts.id')),
        sa.Column('root_id', sa.String(32), nullable=False),
        sa.Column('filename', sa.String(80), nullable=False, unique=True),
        sa.Column('kind', sa.String(16), nullable=False), sa.Column('state', sa.String(24), nullable=False),
        sa.Column('profile', sa.String(16)), sa.Column('source_artifact_id', sa.String(32)),
        sa.Column('bytes', sa.BigInteger(), nullable=False), sa.Column('duration', sa.Float()),
        sa.Column('codecs', sa.JSON(), nullable=False), sa.Column('reason', sa.String(64)))
    op.create_index('ix_recording_artifacts_recording_id', 'recording_artifacts', ['recording_id'])


def downgrade():
    op.drop_table('recording_artifacts')
    op.drop_table('recording_attempts')
    op.drop_table('recordings')
    with op.batch_alter_table('epg_sources') as batch:
        batch.drop_constraint('uq_epg_sources_recording_uuid', type_='unique')
        batch.drop_column('recording_uuid')

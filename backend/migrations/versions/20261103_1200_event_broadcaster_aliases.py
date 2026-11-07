"""Broadcaster aliases: one reviewed link applies to every event of a source."""
from alembic import op
import sqlalchemy as sa

revision = '20261103_1200'
down_revision = '20261030_1300'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('event_broadcaster_aliases',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('source_id', sa.String(length=160), nullable=False),
        sa.Column('label', sa.String(length=200), nullable=False),
        sa.Column('normalized_label', sa.String(length=200), nullable=False),
        sa.Column('target', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('source_id', 'normalized_label', name='uq_event_broadcaster_alias'))
    op.create_index('ix_event_broadcaster_aliases_source_id', 'event_broadcaster_aliases', ['source_id'])


def downgrade():
    op.drop_index('ix_event_broadcaster_aliases_source_id', table_name='event_broadcaster_aliases')
    op.drop_table('event_broadcaster_aliases')

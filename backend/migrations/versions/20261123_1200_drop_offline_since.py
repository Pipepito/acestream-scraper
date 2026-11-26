"""One streak of failed checks, not two.

``offline_since`` was a second streak, opened by its own rule inside the
repository and read only by the cleanup. The cleanup now asks
``source_health`` (``failing_since``), so the column goes. The downgrade
brings it back empty: its age was never recoverable.
"""
from alembic import op
import sqlalchemy as sa

revision = '20261123_1200'
down_revision = '20261113_1400'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.drop_column('offline_since')


def downgrade():
    with op.batch_alter_table('acestream_channels') as batch:
        batch.add_column(sa.Column('offline_since', sa.DateTime(timezone=True), nullable=True))

"""Persist W3U hierarchy independently of TV channels."""
from alembic import op
import sqlalchemy as sa

revision = '20261022_1200'
down_revision = '20261021_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('w3u_catalogues',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(2048)),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('selected_branches', sa.JSON(), nullable=False),
        sa.Column('mode', sa.String(16), nullable=False),
        sa.Column('refresh_enabled', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table('w3u_catalogues')

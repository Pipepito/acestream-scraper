"""
Alembic migration for activity_log table
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_activity_log_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'activity_log',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True, nullable=False),
        sa.Column('type', sa.String(32), nullable=False, index=True),
        sa.Column('message', sa.String(255), nullable=False),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('user', sa.String(64), nullable=True),
    )

def downgrade():
    op.drop_table('activity_log')

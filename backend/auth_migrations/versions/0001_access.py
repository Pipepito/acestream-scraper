"""Independent account, session and credential store."""
from alembic import op
import sqlalchemy as sa

revision = 'access_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('access_state', sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('mode', sa.String(16), nullable=False), sa.Column('policy', sa.Text, nullable=False))
    op.create_table('users', sa.Column('id', sa.String(32), primary_key=True),
                    sa.Column('username', sa.String(64), unique=True, nullable=False),
                    sa.Column('password_hash', sa.Text, nullable=False),
                    sa.Column('administrator', sa.Boolean, nullable=False),
                    sa.Column('enabled', sa.Boolean, nullable=False),
                    sa.Column('permissions', sa.Text, nullable=False))
    op.create_table('sessions', sa.Column('id', sa.String(64), primary_key=True),
                    sa.Column('user_id', sa.String(32), sa.ForeignKey('users.id'), nullable=False),
                    sa.Column('created_at', sa.Float, nullable=False), sa.Column('last_seen', sa.Float, nullable=False),
                    sa.Column('expires_at', sa.Float, nullable=False))
    op.create_index('ix_access_sessions_user', 'sessions', ['user_id'])
    op.create_table('credentials', sa.Column('id', sa.String(32), primary_key=True),
                    sa.Column('digest', sa.String(64), unique=True, nullable=False),
                    sa.Column('user_id', sa.String(32), sa.ForeignKey('users.id'), nullable=False),
                    sa.Column('label', sa.String(80), nullable=False), sa.Column('kind', sa.String(16), nullable=False),
                    sa.Column('created_at', sa.Float, nullable=False))


def downgrade():
    raise RuntimeError('Resetting access storage would expose a protected installation; restore a protected backup instead')

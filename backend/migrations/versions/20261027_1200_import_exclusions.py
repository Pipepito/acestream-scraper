"""Add non-destructive import policy; downgrade removes policy only."""
from alembic import op
import sqlalchemy as sa
revision = '20261027_1200'
down_revision = '20261026_1200'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("telegram_sources", sa.Column("excluded_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_table('import_policy_state', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.CheckConstraint('id = 1', name='ck_import_policy_singleton'))
    op.execute('INSERT INTO import_policy_state (id, revision) VALUES (1, 0)')
    op.create_table('import_exclusion_rules', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(32), nullable=False), sa.Column('value', sa.String(256), nullable=False),
        sa.Column('match_value', sa.String(768), nullable=False), sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('note', sa.String(500)), sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('kind', 'match_value', name='uq_import_exclusion_match'),
        sa.CheckConstraint("kind IN ('name_contains', 'name_equals', 'stream_id_equals')", name='ck_import_exclusion_kind'))
    op.create_index('ix_import_exclusion_rules_enabled', 'import_exclusion_rules', ['enabled'])


def downgrade():
    with op.batch_alter_table("telegram_sources") as batch:
        batch.drop_column("excluded_count")
    op.drop_table('import_exclusion_rules')
    op.drop_table('import_policy_state')

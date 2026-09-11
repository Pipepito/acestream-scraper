"""
Add the base_urls table (#62): named stream base-URL patterns with a
default. Seeds one row from the legacy base_url setting so existing
deployments keep generating identical links.
"""
from alembic import op
import sqlalchemy as sa


revision = '20260824_1200'
down_revision = '20260824_1000'
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table('base_urls'):
        op.create_table(
            'base_urls',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('name', sa.String(length=255), nullable=False, unique=True),
            sa.Column('pattern', sa.String(length=1024), nullable=False),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    bind = op.get_bind()
    count = bind.execute(sa.text("SELECT COUNT(*) FROM base_urls")).scalar()
    if count == 0:
        legacy = None
        if _has_table('settings'):
            legacy = bind.execute(
                sa.text("SELECT value FROM settings WHERE key = 'base_url'")
            ).scalar()
        bind.execute(
            sa.text(
                "INSERT INTO base_urls (name, pattern, is_default) "
                "VALUES (:name, :pattern, :is_default)"
            ),
            {"name": "Default", "pattern": legacy or "acestream://", "is_default": True},
        )


def downgrade() -> None:
    if _has_table('base_urls'):
        op.drop_table('base_urls')

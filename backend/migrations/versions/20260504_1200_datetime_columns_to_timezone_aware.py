"""Make all DateTime columns timezone-aware.

Revision ID: 20260504_1200
Revises: 20260423_1345

Background
----------

The runtime previously declared all timestamp columns as naive
``DateTime()`` and relied on ``datetime.utcnow()`` (deprecated since
Python 3.12) to populate them. As part of the v2 release prep we removed
every ``datetime.utcnow()`` call site in favour of
``datetime.now(timezone.utc)`` and re-typed the model columns as
``DateTime(timezone=True)``.

What this migration does
------------------------

For every existing column we promote the SQLAlchemy column type to
``DateTime(timezone=True)`` so the model definition and the database
metadata stay aligned. Alembic's ``alter_column(..., type_=...)`` is
used inside ``op.batch_alter_table`` so SQLite (the canonical runtime
backend) can apply the change via its standard table-rebuild path.

For SQLite specifically the on-disk representation does not change —
SQLite stores datetimes as ISO-8601 text either way. The migration
keeps Alembic's metadata in sync with the model and unlocks future
moves to a tz-aware backend (e.g. PostgreSQL) without a second
schema-shape migration.

Existing rows store naive datetimes; SQLAlchemy returns them as naive
on read, while new writes from runtime code will include ``+00:00``
timezone info. Comparisons in the codebase happen either via SQL (text
compare on SQLite — works for both) or via ``datetime.now(timezone.utc)
- timedelta(...)`` cutoffs that are pushed into the WHERE clause (also
SQL-side). No Python-side aware-vs-naive arithmetic exists in the
runtime, so the transitional read mix is benign.

The ``activity_log.timestamp`` column was already
``DateTime(timezone=True)`` and is left untouched here.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260504_1200'
down_revision = '20260423_1345'
branch_labels = None
depends_on = None


# Tables and the columns within each that need to flip to tz-aware.
_TZ_AWARE_COLUMNS = {
    "scraped_urls": ("last_processed", "last_scraped", "added_at"),
    "acestream_channels": ("last_seen", "last_checked"),
    "epg_sources": ("last_updated",),
    "tv_channels": ("created_at", "updated_at"),
    "epg_channels": ("created_at", "updated_at"),
    "epg_programs": ("start_time", "end_time"),
}


def _inspector():
    return sa.inspect(op.get_bind())


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = _inspector()
    if table_name not in inspector.get_table_names():
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _alter(table_name: str, columns: tuple, *, timezone: bool) -> None:
    targets = [name for name in columns if _column_exists(table_name, name)]
    if not targets:
        return

    with op.batch_alter_table(table_name) as batch:
        for column_name in targets:
            batch.alter_column(
                column_name,
                type_=sa.DateTime(timezone=timezone),
                existing_type=sa.DateTime(timezone=not timezone),
                existing_nullable=True,
            )


def upgrade() -> None:
    for table_name, columns in _TZ_AWARE_COLUMNS.items():
        _alter(table_name, columns, timezone=True)


def downgrade() -> None:
    for table_name, columns in _TZ_AWARE_COLUMNS.items():
        _alter(table_name, columns, timezone=False)

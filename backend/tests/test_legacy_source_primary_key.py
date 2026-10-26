"""Old source keys must migrate without conflicting reflected PK metadata."""
import importlib.util
from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.mark.parametrize('integer_id', [False, True])
@pytest.mark.parametrize('named_key', [False, True])
def test_legacy_source_key_round_trip_preserves_rows(tmp_path, integer_id, named_key):
    migration_path = Path(__file__).parents[1] / 'migrations/versions/KbBg5DH3tkxp_add_guid_id_to_scraped_urls.py'
    spec = importlib.util.spec_from_file_location('source_key_migration', migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine(f'sqlite:///{tmp_path / "legacy.db"}')
    try:
        with engine.begin() as connection:
            metadata = sa.MetaData()
            columns = [sa.Column('url', sa.String(255), nullable=False)]
            if integer_id:
                columns.append(sa.Column('id', sa.Integer, nullable=False))
            columns.append(sa.PrimaryKeyConstraint(
                'id' if integer_id else 'url', name='legacy_source_pk' if named_key else None,
            ))
            table = sa.Table('scraped_urls', metadata, *columns)
            table.create(connection)
            rows = [{'url': 'https://example.test/one'}, {'url': 'https://example.test/two'}]
            if integer_id:
                for index, row in enumerate(rows, 1):
                    row['id'] = index
            connection.execute(table.insert(), rows)
            migration.op = Operations(MigrationContext.configure(connection))

            for action in (migration.upgrade, migration.upgrade, migration.downgrade, migration.upgrade):
                action()
                assert sa.inspect(connection).get_pk_constraint('scraped_urls')['constrained_columns'] == ['id'], action.__name__
                saved = connection.execute(sa.text('SELECT id, url FROM scraped_urls ORDER BY url')).all()
                assert [row.url for row in saved] == [row['url'] for row in rows]
                assert len({row.id for row in saved}) == 2
                if action != migration.downgrade:
                    assert all(UUID(row.id) for row in saved)
    finally:
        engine.dispose()

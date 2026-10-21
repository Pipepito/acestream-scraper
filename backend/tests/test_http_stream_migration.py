"""Preserve existing rows and nullable URL metadata through the real upgrade path."""
from sqlalchemy import create_engine, inspect, text
from migration_test_utils import database_url_for, upgrade_to_revision, downgrade_to_revision


def test_http_columns_upgrade_downgrade_preserves_catalogue(tmp_path):
    path = tmp_path / 'http-upgrade.sqlite'
    upgrade_to_revision(path, '20260928_1200')
    engine = create_engine(database_url_for(path))
    try:
        with engine.begin() as db:
            db.execute(text("INSERT INTO acestream_channels (id,name,is_active,is_online) VALUES (:id,'Existing',1,1)"), {'id': 'a' * 40})
        upgrade_to_revision(path, '20261021_1200')
        with engine.begin() as db:
            row = db.execute(text('SELECT name,is_online,stream_url,stream_headers FROM acestream_channels')).one()
            assert tuple(row) == ('Existing', 1, None, None)
            db.execute(text('UPDATE acestream_channels SET stream_url=:url,stream_headers=:headers'),
                       {'url': 'https://cdn.example/live.m3u8', 'headers': '{"Referer":"https://example.com/"}'})
        downgrade_to_revision(path, '20260928_1200')
        assert 'stream_url' not in {column['name'] for column in inspect(engine).get_columns('acestream_channels')}
        with engine.connect() as db:
            assert tuple(db.execute(text('SELECT name,is_online FROM acestream_channels')).one()) == ('Existing', 1)
        upgrade_to_revision(path, '20261021_1200')
        with engine.connect() as db:
            assert db.execute(text('SELECT stream_url FROM acestream_channels')).scalar() is None
    finally:
        engine.dispose()

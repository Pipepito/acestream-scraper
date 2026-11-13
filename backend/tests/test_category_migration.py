"""Real previous-head upgrade preserves legacy labels and classification ownership."""
from sqlalchemy import create_engine, inspect, text
from migration_test_utils import database_url_for, upgrade_to_revision, downgrade_to_revision, upgrade_to_head


def test_category_migration_preserves_scalar_and_catalogue(tmp_path):
    path = tmp_path / 'categories.sqlite'
    upgrade_to_revision(path, '20261109_1200')
    engine = create_engine(database_url_for(path))
    try:
        with engine.begin() as db:
            db.execute(text("INSERT INTO tv_channels (id,name,category) VALUES (1,'Custom','My collection'),(2,'Blank',NULL)"))
            db.execute(text("INSERT INTO epg_sources (id,name,url) VALUES (1,'Guide','https://example.test/guide')"))
            db.execute(text("INSERT INTO epg_channels (id,epg_source_id,channel_xml_id,name) VALUES (1,1,'one','One')"))
            db.execute(text("INSERT INTO epg_programs (id,epg_channel_id,start_time,end_time,title,category) VALUES (1,1,'2026-11-09 00:00:00','2026-11-09 01:00:00','First','Cine, Acción'),(2,1,'2026-11-09 01:00:00','2026-11-09 02:00:00','Next',NULL)"))
        upgrade_to_head(path)
        with engine.connect() as db:
            assert list(db.execute(text('SELECT category,category_origin,category_revision FROM tv_channels ORDER BY id'))) == [('My collection', 'legacy', 0), (None, 'legacy', 0)]
            assert list(db.execute(text('SELECT program_id,position,label,language FROM epg_program_categories'))) == [(1, 0, 'Cine, Acción', None)]
        downgrade_to_revision(path, '20261109_1200')
        assert 'epg_program_categories' not in inspect(engine).get_table_names()
        with engine.connect() as db:
            assert db.execute(text('SELECT category FROM epg_programs WHERE id=1')).scalar() == 'Cine, Acción'
        upgrade_to_head(path)
    finally:
        engine.dispose()

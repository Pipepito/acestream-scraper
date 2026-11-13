from sqlalchemy import create_engine, text
from migration_test_utils import upgrade_to_revision, downgrade_to_revision, database_url_for


def guide(name='Sports One', xml_id='sports.es', title='First schedule'):
    return f'''<tv><channel id="{xml_id}"><display-name>{name}</display-name></channel>
      <programme channel="{xml_id}" start="20261109190000 +0000" stop="20261109200000 +0000"><title>{title}</title></programme></tv>'''.encode()


def test_shared_channel_inventory_keeps_programmes_and_source_deletion_independent(client, db_session):
    from app.models.models import EPGSource, EPGChannel, EPGChannelIdentity, EPGProgram
    from app.services.epg_service import EPGService
    sources = [EPGSource(name=f'Guide {i}', url=f'https://example.org/{i}') for i in range(3)]
    db_session.add_all(sources)
    db_session.commit()
    service = EPGService(db_session)
    service._process_epg_xml(sources[0].id, guide())
    service._process_epg_xml(sources[1].id, guide(name='  SPORTS   ONE ', title='Second schedule'))
    service._process_epg_xml(sources[2].id, guide(name='Sports One UK', title='Regional schedule'))
    data = client.get('/api/v1/epg/channels', params={'limit': 1}).json()
    assert data['total'] == 2 and len(data['items']) == 1
    shared = data['items'][0]
    assert len(shared['sources']) == 2
    assert db_session.query(EPGChannelIdentity).count() == 2
    assert db_session.query(EPGChannel).count() == 3  # Source memberships, not inventory channels.
    from app.repositories.epg_inventory_repository import EPGInventoryRepository
    assert EPGInventoryRepository(db_session).count() == 2
    assert len(client.get(f'/api/v1/epg/channels/{shared["id"]}').json()['sources']) == 2
    assert client.get('/api/v1/epg/channels', params={'source_id': sources[1].id}).json()['total'] == 1
    service._process_epg_xml(sources[0].id, guide(title='Corrected first schedule'))
    assert {row.title for row in db_session.query(EPGProgram)} == {'Corrected first schedule', 'Second schedule', 'Regional schedule'}
    service.delete_source(sources[0].id)
    assert {row.title for row in db_session.query(EPGProgram)} == {'Second schedule', 'Regional schedule'}
    data = client.get('/api/v1/epg/channels').json()
    assert data['total'] == 2
    assert all(len(row['sources']) == 1 for row in data['items'])


def test_renamed_membership_leaves_group_and_different_ids_never_merge(db_session):
    from app.models.models import EPGSource
    from app.services.epg_service import EPGService
    sources = [EPGSource(name=str(i), url=f'https://example.org/{i}') for i in range(2)]
    db_session.add_all(sources)
    db_session.commit()
    service = EPGService(db_session)
    for source in sources:
        service._process_epg_xml(source.id, guide())
    assert service.get_channels()[1] == 1
    service._process_epg_xml(sources[1].id, guide(name='Different regional channel'))
    assert service.get_channels()[1] == 2
    service._process_epg_xml(sources[1].id, guide(xml_id='other.es'))
    assert service.get_channels()[1] == 3


def test_identity_upgrade_backfills_without_changing_memberships_or_programmes(tmp_path):
    path = tmp_path / 'epg.sqlite'
    upgrade_to_revision(path, '20261107_1200')
    engine = create_engine(database_url_for(path))
    with engine.begin() as db:
        db.execute(text("INSERT INTO epg_sources (id, url, name) VALUES (1, 'https://a.example', 'A'), (2, 'https://b.example', 'B')"))
        db.execute(text("INSERT INTO epg_channels (id, epg_source_id, channel_xml_id, name) VALUES (10, 1, 'one', 'Sports One'), (20, 2, 'one', ' SPORTS ONE ')"))
        db.execute(text("INSERT INTO epg_programs (id, epg_channel_id, start_time, end_time, title) VALUES (1, 20, '2026-11-09 19:00:00', '2026-11-09 20:00:00', 'Saved guide')"))
        db.execute(text("INSERT INTO tv_channels (id, name, epg_id, epg_source_id) VALUES (1, 'TV', 'one', 2)"))
    upgrade_to_revision(path, 'head')
    with engine.connect() as db:
        assert db.execute(text('SELECT count(*) FROM epg_channel_identities')).scalar() == 1
        assert db.execute(text('SELECT count(distinct identity_id) FROM epg_channels')).scalar() == 1
        assert db.execute(text('SELECT epg_channel_id FROM epg_programs')).scalar() == 20
        assert db.execute(text('SELECT epg_source_id FROM tv_channels')).scalar() == 2
        assert list(db.execute(text('PRAGMA foreign_key_check'))) == []
    downgrade_to_revision(path, '20261107_1200')
    with engine.connect() as db:
        assert db.execute(text('SELECT epg_channel_id FROM epg_programs')).scalar() == 20
        assert db.execute(text('SELECT count(*) FROM epg_channels')).scalar() == 2
    engine.dispose()

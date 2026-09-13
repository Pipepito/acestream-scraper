from app.models.models import EPGChannel, EPGSource, TVChannel
from app.services.epg_link_service import EPGLinkService
from app.services.epg_service import EPGService


def inventory(db):
    sources = [EPGSource(name=name, url=f'https://example.com/{name}', enabled=True) for name in ['one', 'two']]
    db.add_all(sources)
    db.flush()
    channels = [EPGChannel(name=name, channel_xml_id=xml, epg_source_id=source.id)
                for source, name, xml in [(sources[0], 'Televisión', 'old'), (sources[1], 'Television', 'new')]]
    db.add_all(channels)
    tv = TVChannel(name='Televisión', epg_id='old', epg_source_id=sources[0].id, is_favorite=True, channel_number=7)
    db.add(tv)
    db.commit()
    return sources, tv


def test_delete_source_relinks_normalized_name_preserving_tv(db_session):
    sources, tv = inventory(db_session)
    identity = tv.id
    assert EPGService(db_session).delete_source(sources[0].id)
    db_session.refresh(tv)
    assert (tv.id, tv.epg_id, tv.epg_source_id, tv.is_favorite, tv.channel_number) == (identity, 'new', sources[1].id, True, 7)


def test_valid_link_stays_and_ambiguous_name_is_not_repaired(db_session):
    sources, tv = inventory(db_session)
    assert EPGLinkService(db_session).repair() == 0
    tv.epg_source_id = None
    tv.epg_id = None
    assert EPGLinkService(db_session).repair() == 0
    assert tv.epg_source_id is None


def test_auto_map_repairs_already_orphaned_channels(db_session):
    sources, tv = inventory(db_session)
    tv.epg_source_id = None
    tv.epg_id = 'new'
    db_session.commit()
    result = EPGService(db_session).auto_map_channels()
    assert result['auto_mapped_count'] == 1
    assert tv.epg_source_id == sources[1].id


def test_refresh_repairs_orphan_without_recreating_tv(db_session):
    sources, tv = inventory(db_session)
    tv.epg_id = 'new'
    tv.epg_source_id = None
    db_session.commit()
    EPGService(db_session)._process_epg_xml(sources[1].id, b'<tv><channel id="new"><display-name>Television</display-name></channel></tv>')
    assert tv.epg_source_id == sources[1].id


def test_create_from_epg_reuses_normalized_name(db_session):
    from app.services.tvchannel_service import TVChannelService
    sources, tv = inventory(db_session)
    EPGService(db_session).delete_source(sources[0].id)
    epg = db_session.query(EPGChannel).filter_by(epg_source_id=sources[1].id).one()
    result = TVChannelService(db_session).create_tv_channels_from_epg([epg.id])
    assert result['created_count'] == 0
    assert db_session.query(TVChannel).count() == 1

"""The name a TV channel is born with when an import creates it from a guide.

A guide that uses the id as display name (`Alpha.TV`), and a scrape
of its list created 131 TV channels named like that. When the guide gives
nothing better than its id, the stream's own name is used. A name set later
in the interface always wins: an import never renames an existing channel.
"""
from app.models.models import EPGChannel, EPGSource, TVChannel
from app.services.epg_service import EPGService
from app.services.m3u_service import M3UService
from app.services.tvchannel_service import TVChannelService


def _guide(db, channels):
    source = EPGSource(url='https://example.com/epg.xml', name='Guide', enabled=True)
    db.add(source)
    db.flush()
    for xml_id, name in channels:
        db.add(EPGChannel(epg_source_id=source.id, channel_xml_id=xml_id, name=name))
    db.commit()


def _import(db, playlist):
    service = M3UService()
    channels = service.extract_channels_from_content(playlist)
    service.auto_create_tv_channels_from_epg(db, channels, EPGService(db), TVChannelService(db))
    db.commit()
    return {tv.epg_id: tv.name for tv in db.query(TVChannel).all()}


LIST = """#EXTM3U
#EXTINF:-1 tvg-id="Alpha.TV" group-title="Group",Alpha
acestream://{a}
#EXTINF:-1 tvg-id="Beta HD",Beta FHD
acestream://{b}
#EXTINF:-1 tvg-id="Gamma.TV",GAMMA FHD --> SOME LABEL
acestream://{c}
""".format(a='1' * 40, b='2' * 40, c='3' * 40)


def test_SI_LA_GUIA_SOLO_DA_SU_ID_SE_USA_EL_NOMBRE_DE_LA_EMISION(db_session):
    _guide(db_session, [('Alpha.TV', 'Alpha.TV')])
    assert _import(db_session, LIST)['Alpha.TV'] == 'Alpha'


def test_UN_NOMBRE_DE_GUIA_DE_VERDAD_SE_RESPETA(db_session):
    """A publisher's `Beta HD` is named `Beta`: that one is kept."""
    _guide(db_session, [('Beta HD', 'Beta')])
    assert _import(db_session, LIST)['Beta HD'] == 'Beta'


def test_LO_QUE_EL_PUBLICADOR_PONE_TRAS_LA_FLECHA_NO_ES_EL_NOMBRE(db_session):
    _guide(db_session, [('Gamma.TV', 'Gamma.TV')])
    assert _import(db_session, LIST)['Gamma.TV'] == 'GAMMA FHD'


def test_UN_NOMBRE_PUESTO_A_MANO_GANA_AL_VOLVER_A_IMPORTAR(db_session):
    _guide(db_session, [('Alpha.TV', 'Alpha.TV')])
    _import(db_session, LIST)
    tv = db_session.query(TVChannel).filter(TVChannel.epg_id == 'Alpha.TV').one()
    tv.name = 'Alpha Renamed'
    db_session.commit()
    names = _import(db_session, LIST)
    assert names['Alpha.TV'] == 'Alpha Renamed'
    assert db_session.query(TVChannel).filter(TVChannel.epg_id == 'Alpha.TV').count() == 1

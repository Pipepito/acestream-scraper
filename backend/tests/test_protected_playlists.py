import asyncio
from starlette.requests import Request
from app.models.models import AcestreamChannel, TVChannel
from app.services.watch_service import ProtectedPlaylistService
from app.repositories.watch_repository import WatchRepository


def test_protected_playlist_retains_filters_and_guide_without_upstream_secrets(db_session):
    tv = TVChannel(name='Selected', channel_number=7, category='Sport', is_active=True, is_favorite=True)
    other = TVChannel(name='Excluded', channel_number=8, category='News', is_active=True)
    db_session.add_all([tv, other])
    db_session.flush()
    db_session.add_all([
        AcestreamChannel(id='a' * 40, name='Selected source', tv_channel_id=tv.id, source_url='fixture', is_active=True, is_online=True, group='Sport', tvg_id='guide-selected'),
        AcestreamChannel(id='url:' + 'b' * 40, name='HTTP source', tv_channel_id=tv.id, source_url='fixture', is_active=True, is_online=True, group='Sport', stream_url='https://private.example/video?secret=do-not-export', stream_headers={'Referer': 'private-header'}),
        AcestreamChannel(id='c' * 40, name='Other source', tv_channel_id=other.id, source_url='fixture', is_active=True, is_online=True, group='News'),
    ])
    db_session.commit()
    request = Request({'type': 'http', 'method': 'GET', 'path': '/tv/api/v1/playlists/m3u', 'root_path': '/tv', 'scheme': 'https',
        'server': ('testserver', 443), 'headers': [], 'query_string': b'', 'state': {'access_mode': 'accounts', 'playback_token': 'playback-only'}})
    service = ProtectedPlaylistService(db_session, request, 'https://testserver/tv')
    body = asyncio.run(service.generate_playlist(base_url='https://testserver/tv/tuner/channel/{tv_channel_id}.ts',
        group='Sport', only_online=False, per_source=True, epg_url='https://testserver/tv/api/v1/epg/xml?token=playback-only'))
    assert 'Selected' in body and 'Excluded' not in body and 'tvg-chno="7"' in body
    assert 'guide-selected' in body and 'url-tvg="https://testserver/tv/api/v1/epg/xml?token=playback-only"' in body
    urls = [line for line in body.splitlines() if line and not line.startswith('#')]
    assert len(urls) == 3
    assert all(url.startswith('https://testserver/tv/tuner/') and 'token=playback-only' in url for url in urls)
    assert not any(secret in body for secret in ('private.example', 'do-not-export', 'private-header'))
    assert WatchRepository(db_session).channels().total == 3

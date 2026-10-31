"""Watch catalogue and protected exports reuse the normal playlist selection."""
import asyncio
from urllib.parse import quote
from fastapi import HTTPException
from app.config.database import SessionLocal
from app.repositories.watch_repository import WatchRepository
from app.services.playlist_service import PlaylistService


def imported_stream(content_id):
    with SessionLocal() as db:
        return WatchRepository(db).imported_stream(content_id)


class ProtectedPlaylistService(PlaylistService):
    """Preserve guide identities and filters without exporting upstream secrets."""
    def __init__(self, db, request, base):
        super().__init__(db, live_base_url=base)
        self.request = request

    def _stream_link(self, base_url, channel_id, pid=None, *, tv_channel_id=None,
                     stream_url=None, stream_headers=None, live_base_url=None):
        from app.api.auth import authenticated_player_url
        if '{tv_channel_id}' in base_url and tv_channel_id is not None:
            path = '/tuner/channel/' + str(tv_channel_id) + '.ts'
        elif stream_url:
            path = '/tuner/source/' + quote(channel_id, safe=':') + '.ts'
        else:
            path = '/tuner/stream/' + channel_id + '.ts'
        return authenticated_player_url(self.request, self.live_base_url + path)


def safe_playlist(request):
    """Run in a worker: legacy playlist methods perform synchronous DB reads."""
    from app.api.auth import authenticated_player_url
    from app.repositories.settings_repository import SettingsRepository
    from app.services.public_url_service import resolve_public_base_url
    query = request.query_params
    def boolean(name, default=False):
        value = query.get(name)
        if value is None:
            return default
        if value.lower() not in ('true', 'false', '1', '0'):
            raise HTTPException(422, 'Invalid playlist option: ' + name)
        return value.lower() in ('true', '1')
    with SessionLocal() as db:
        base = resolve_public_base_url(request, SettingsRepository(db)).url
        service = ProtectedPlaylistService(db, request, base)
        options = dict(search=query.get('search', '')[:200], base_url=base + '/tuner/channel/{tv_channel_id}.ts',
                       epg_url=authenticated_player_url(request, base + '/api/v1/epg/xml'))
        if '/tv-channels/' in request.url.path:
            result = service.generate_tv_channels_playlist(**options, favorites_only=boolean('favorites_only'))
        elif '/all-streams/' in request.url.path:
            result = service.generate_all_streams_playlist(**options, include_unassigned=boolean('include_unassigned', True))
        else:
            result = service.generate_playlist(**options, group=query.get('group'), only_online=boolean('only_online', True),
                include_unassigned=boolean('include_unassigned'), per_source=boolean('per_source'), favorites_only=boolean('favorites_only'),
                include_groups=query['include_groups'].split(',') if query.get('include_groups') else None,
                exclude_groups=query['exclude_groups'].split(',') if query.get('exclude_groups') else None)
        return asyncio.run(result)

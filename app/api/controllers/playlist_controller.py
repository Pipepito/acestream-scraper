from flask_restx import Namespace, Resource, fields, reqparse
from flask import Response, redirect, request, current_app
import time
from datetime import datetime, timezone
from app.models import AcestreamChannel
from app.services.playlist_service import PlaylistService
from app.repositories import URLRepository
from app.services import ScraperService

api = Namespace('playlists', description='Playlist management operations')

playlist_parser = reqparse.RequestParser()
playlist_parser.add_argument('refresh', type=bool, required=False, default=False,
                          help='Whether to refresh the playlist before returning')
playlist_parser.add_argument('search', type=str, required=False,
                          help='Filter channels by name')

@api.route('/m3u')
class M3UPlaylist(Resource):
    @api.doc('get_m3u_playlist')
    @api.expect(playlist_parser)
    def get(self):
        """Get M3U playlist of all channels"""
        args = playlist_parser.parse_args()
        refresh = args.get('refresh', False)
        search = args.get('search', None)
        
        if refresh:
            try:
                from app.views.main import task_manager
                
                url_repository = URLRepository()
                urls = url_repository.get_enabled()
                
                for url in urls:
                    task_manager.add_url(url.url)
            except Exception as e:
                api.abort(500, f"Error during playlist refresh: {str(e)}")
        
        playlist_service = PlaylistService()
        playlist = playlist_service.generate_playlist(search_term=search)
        
        filename = f"acestream_playlist_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        if search:
            filename += f"_filtered"
        filename += ".m3u"
        
        return Response(
            playlist,
            mimetype="audio/x-mpegurl",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

@api.route('/channels')
class PlaylistChannels(Resource):
    @api.doc('get_playlist_channels')
    def get(self):
        """Get list of all channels suitable for playlist generation"""
        channels = AcestreamChannel.query.filter_by(status='active').all()
        
        result = []
        for channel in channels:
            result.append({
                'id': channel.id,
                'name': channel.name,
                'is_online': channel.is_online,
                'group': channel.group or 'Uncategorized',
                'logo': channel.logo,
                'tvg_id': channel.tvg_id,
                'tvg_name': channel.tvg_name
            })
            
        return result
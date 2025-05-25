from flask_restx import Namespace, Resource, fields, reqparse
from flask import Response, redirect, request, current_app
import time
from datetime import datetime, timezone
from app.models import AcestreamChannel
from app.services.playlist_service import PlaylistService
from app.repositories import URLRepository
from app.services import ScraperService
from app.repositories.tv_channel_repository import TVChannelRepository

api = Namespace('playlists', description='Playlist management operations')

playlist_parser = reqparse.RequestParser()
playlist_parser.add_argument('refresh', type=bool, required=False, default=False,
                          help='Whether to refresh the playlist before returning')
playlist_parser.add_argument('search', type=str, required=False,
                          help='Filter channels by name')
playlist_parser.add_argument('favorites_only', type=bool, required=False, default=False,
                          help='Filter to show only favorite channels')

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

@api.route('/tv-channels/m3u')
class TVChannelsPlaylist(Resource):
    @api.doc('get_tv_channels_playlist')
    @api.expect(playlist_parser)
    def get(self):
        """Get M3U playlist of TV channels with their best acestreams"""
        args = playlist_parser.parse_args()
        search = args.get('search', None)
        favorites_only = args.get('favorites_only', False)
        
        playlist_service = PlaylistService()
        playlist = playlist_service.generate_tv_channels_playlist(
            search_term=search,
            favorites_only=favorites_only
        )
        
        filename = f"tv_channels_playlist_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        if search:
            filename += f"_filtered"
        if favorites_only:
            filename += "_favorites"
        filename += ".m3u"
        
        return Response(
            playlist,
            mimetype="audio/x-mpegurl",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

@api.route('/epg.xml')
class EPGXmlGuide(Resource):
    @api.doc('get_epg_xml_guide')
    @api.expect(playlist_parser)
    def get(self):
        """Get XML EPG guide for channels with EPG data"""
        args = playlist_parser.parse_args()
        search = args.get('search', None)
        favorites_only = args.get('favorites_only', False)
        
        playlist_service = PlaylistService()
        xml_guide = playlist_service.generate_epg_xml(
            search_term=search,
            favorites_only=favorites_only
        )
        
        filename = f"epg_guide_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        if search:
            filename += f"_filtered"
        if favorites_only:
            filename += "_favorites"
        filename += ".xml"
        
        return Response(
            xml_guide,
            mimetype="application/xml",
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

@api.route('/all-streams/m3u')
class AllStreamsPlaylist(Resource):
    @api.doc('get_all_streams_playlist')
    @api.expect(playlist_parser)
    def get(self):
        """Get M3U playlist of all acestreams with proper channel numbering (TV channels + unassigned)"""
        args = playlist_parser.parse_args()
        search = args.get('search', None)
        include_unassigned = request.args.get('include_unassigned', 'true').lower() == 'true'
        
        playlist_service = PlaylistService()
        playlist = playlist_service.generate_all_streams_playlist(
            search_term=search,
            include_unassigned=include_unassigned
        )
        
        filename = f"all_streams_playlist_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        if search:
            filename += f"_filtered"
        if not include_unassigned:
            filename += "_assigned_only"
        filename += ".m3u"
        
        return Response(
            playlist,
            mimetype="audio/x-mpegurl",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
# app/views/api.py (create this file if it doesn't exist)

from flask import Blueprint, jsonify, request, current_app
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..utils.config import Config
from ..repositories import URLRepository, ChannelRepository, SettingsRepository
from ..services import PlaylistService

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/stats/')
def get_stats():
    """Get scraping statistics."""
    urls = ScrapedURL.query.all()
    channels = AcestreamChannel.query.all()
    config = Config()
    
    # Count channels by status
    total_checked = sum(1 for ch in channels if ch.last_checked is not None)
    online_channels = sum(1 for ch in channels if ch.is_online)
    
    url_stats = []
    for url in urls:
        channel_count = AcestreamChannel.query.filter_by(source_url=url.url).count()
        
        url_stats.append({
            'url': url.url,
            'status': url.status,
            'last_processed': url.last_processed.isoformat() if url.last_processed else None,
            'channel_count': channel_count,
            'enabled': url.enabled
        })
    
    return jsonify({
        'urls': url_stats,
        'total_channels': len(channels),
        'channels_checked': total_checked,
        'channels_online': online_channels,
        'channels_offline': total_checked - online_channels,
        'base_url': config.base_url,
        'ace_engine_url': config.ace_engine_url,
        'rescrape_interval': config.rescrape_interval
    })

@bp.route('/playlists/m3u')
def get_api_playlist():
    """API endpoint for M3U playlist."""
    search = request.args.get('search', None)
    
    # Generate playlist using service
    playlist_service = PlaylistService()
    playlist = playlist_service.generate_playlist(search_term=search)
    
    return playlist, 200, {
        'Content-Type': 'audio/x-mpegurl'
    }
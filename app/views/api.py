# app/views/api.py (create this file if it doesn't exist)

from flask import Blueprint, jsonify, request, current_app
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..utils.config import Config
from ..repositories import URLRepository, ChannelRepository, SettingsRepository
from ..services import PlaylistService, ScraperService  # Add ScraperService import
from ..models.url_types import create_url_object, ZeronetURL, RegularURL
import asyncio  # Add asyncio import for refresh_url function

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
            'id': url.id,
            'url': url.url,
            'url_type': url.url_type,
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

@bp.route('/urls/', methods=['POST'])
def add_url():
    """Add a new URL to scrape."""
    data = request.json
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    url_type = data.get('url_type')
    
    # Require explicit URL type selection
    if not url_type or url_type == 'auto':
        current_app.logger.error("URL type missing or set to 'auto'")
        return jsonify({'error': 'You must explicitly select a URL type (regular or zeronet)'}), 400
    
    # More detailed error logging
    current_app.logger.info(f"Adding URL: {url} with type: {url_type}")
    
    # Validate URL format based on type
    try:
        url_obj = create_url_object(url, url_type)
        current_app.logger.info(f"URL object created successfully: {url_obj.type_name}")
    except ValueError as e:
        current_app.logger.error(f"URL validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error during URL validation: {str(e)}", exc_info=True)
        return jsonify({'error': f'URL validation failed: {str(e)}'}), 500
    
    # Check if URL already exists
    url_repo = URLRepository()
    if url_repo.get_by_url(url):
        current_app.logger.info(f"URL already exists: {url}")
        return jsonify({'error': 'URL already exists'}), 409
    
    try:
        # Use a dedicated session for this operation
        effective_type = url_type if url_type != 'auto' else url_obj.type_name
        current_app.logger.info(f"Adding URL to database with type: {effective_type}")
        
        url_db_obj = url_repo.add(url, effective_type)
        
        # Return success message
        return jsonify({
            'message': 'URL added successfully',
            'url': url_db_obj.url,
            'url_type': url_db_obj.url_type
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error adding URL to database: {str(e)}", exc_info=True)
        # Ensure we rollback any failed transaction
        try:
            url_repo._db.session.rollback()
        except Exception as rollback_error:
            current_app.logger.error(f"Error during rollback: {str(rollback_error)}")
        
        return jsonify({'error': f'Failed to add URL: {str(e)}'}), 500

@bp.route('/urls/<path:url>/refresh', methods=['POST'])
def refresh_url(url):
    """Refresh a specific URL."""
    # Get URL type from database or use auto detection
    url_obj = URLRepository().get_by_url(url)
    url_type = url_obj.url_type if url_obj else 'auto'
    
    try:
        links, status = asyncio.run(ScraperService().scrape_url(url, url_type))
        return jsonify({
            'message': 'URL refreshed successfully',
            'status': status,
            'channels_found': len(links)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
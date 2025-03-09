from flask import Blueprint, render_template, jsonify, request, Response, current_app
from datetime import datetime, timedelta
import asyncio
import logging
import os  # Add this line
import requests  # Add this line too since you're using it
from sqlalchemy import text
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..utils.config import Config
from ..tasks.manager import TaskManager
from ..services import ScraperService, PlaylistService
from ..repositories import URLRepository, ChannelRepository
from ..services.channel_status_service import ChannelStatusService

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)  # Add this line to define logger

# Add a reference to the task manager
task_manager = None

@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@bp.route('/api/stats')
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
            'enabled': url.status != 'disabled'
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

@bp.route('/api/channels')
def get_channels():
    """Get all channels with optional name filter."""
    search = request.args.get('search', '').strip().lower()
    
    query = AcestreamChannel.query
    
    if search:
        # Case-insensitive search on channel name
        query = query.filter(AcestreamChannel.name.ilike(f'%{search}%'))
    
    channels = query.all()
    return jsonify([{
        'id': ch.id,
        'name': ch.name,
        'last_processed': ch.last_processed.isoformat() if ch.last_processed else None,
        'is_online': ch.is_online,
        'last_checked': ch.last_checked.isoformat() if ch.last_checked else None,
        'check_error': ch.check_error
    } for ch in channels])

# Add this new route
@bp.route('/api/channels', methods=['POST'])
def add_channel():
    """Add a channel manually."""
    try:
        data = request.get_json()
        channel_id = data.get('id')
        channel_name = data.get('name')
        
        if not channel_id or not channel_name:
            return jsonify({'error': 'Channel ID and name are required'}), 400
            
        # Use repository to add channel
        channel_repository = ChannelRepository()
        channel = channel_repository.update_or_create(
            channel_id=channel_id,
            name=channel_name,
            source_url='manual'  # Indicate this was manually added
        )
        channel_repository.commit()
        
        return jsonify({
            'message': 'Channel added successfully',
            'channel': {
                'id': channel.id,
                'name': channel.name
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add this new route
@bp.route('/api/channels/<channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    """Delete a channel."""
    try:
        channel_repository = ChannelRepository()
        channel = channel_repository.get_by_id(channel_id)
        
        if not channel:
            return jsonify({'error': 'Channel not found'}), 404
            
        channel_repository.delete(channel)
        channel_repository.commit()
        
        return jsonify({'message': 'Channel deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/urls', methods=['POST'])
def add_url():
    """Add a new URL to scrape."""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    try:
        # Check if URL already exists
        existing_url = ScrapedURL.query.filter_by(url=url).first()
        if (existing_url):
            # Reset status to trigger new scrape
            existing_url.status = 'pending'
            existing_url.error_count = 0
            existing_url.last_error = None
        else:
            # Add new URL to database
            new_url = ScrapedURL(url=url, status='pending')
            db.session.add(new_url)
            
            # Add to config if not already present
            config = Config()
            if url not in config.urls:
                config.add_url(url)
        
        db.session.commit()
        
        # Create asyncio task for immediate processing
        if task_manager and task_manager.running:
            async def process():
                await task_manager.process_url(url)
            
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.create_task(process())
            
        return jsonify({'message': 'URL added successfully and queued for processing'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding URL: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/refresh', methods=['POST'])
def refresh_urls():
    """Force refresh all URLs."""
    try:
        # Reset all URLs except disabled ones to pending status
        urls = ScrapedURL.query.filter(ScrapedURL.status != 'disabled').all()
        
        for url in urls:
            url.status = 'pending'
            url.error_count = 0
            url.last_error = None
        
        db.session.commit()
        
        # Trigger immediate processing if task manager is available
        if task_manager and task_manager.running:
            async def process_all():
                for url in urls:
                    await task_manager.process_url(url.url)
            
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.create_task(process_all())
        
        return jsonify({
            'message': f'Refresh initiated for {len(urls)} URLs',
            'urls': [url.url for url in urls]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/urls/<path:url>', methods=['DELETE', 'PUT'])
def manage_url(url):
    """Manage (delete or update) a URL."""
    try:
        url_obj = ScrapedURL.query.filter_by(url=url).first()
        if not url_obj:
            return jsonify({'error': 'URL not found'}), 404

        if request.method == 'DELETE':
            # Delete the URL and its associated channels
            AcestreamChannel.query.filter_by(source_url=url).delete()
            db.session.delete(url_obj)
            db.session.commit()
            return jsonify({'message': 'URL deleted successfully'})
            
        elif request.method == 'PUT':
            data = request.get_json()
            enabled = data.get('enabled', True)
            
            if not enabled:
                url_obj.status = 'disabled'
            else:
                url_obj.status = 'pending'  # Re-enable and queue for processing
                
            db.session.commit()
            return jsonify({'message': f'URL {"enabled" if enabled else "disabled"} successfully'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/playlist.m3u')
async def get_playlist():
    """Generate and return M3U playlist with optional refresh and filtering."""
    should_refresh = request.args.get('refresh', '').lower() == 'true'
    search = request.args.get('search', '').strip().lower()
    
    if should_refresh:
        scraper_service = ScraperService()
        url_repository = URLRepository()
        urls = url_repository.get_all()
        
        # Process each URL sequentially
        for url in urls:
            if url.status != 'disabled':
                try:
                    await scraper_service.scrape_url(url.url)
                except Exception as e:
                    logger.error(f"Error refreshing URL {url.url}: {e}")
    
    # Generate playlist using service with search parameter
    playlist_service = PlaylistService()
    playlist = playlist_service.generate_playlist(search_term=search)
    
    # Modify filename to indicate if it's filtered
    filename = f"acestream_playlist_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    if search:
        filename += f"_filtered"
    filename += ".m3u"
    
    return Response(
        playlist,
        mimetype='audio/x-mpegurl',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )

@bp.route('/api/config/base_url', methods=['PUT'])
def update_base_url():
    """Update the base URL configuration."""
    try:
        data = request.get_json()
        new_base_url = data.get('base_url')
        
        if not new_base_url:
            return jsonify({'error': 'base_url is required'}), 400
            
        config = Config()
        config._config['base_url'] = new_base_url
        config._save_config()
        
        # Return a sample URL for preview
        return jsonify({
            'message': 'Base URL updated successfully',
            'sample': f"{new_base_url}{'1' * 40}"  # 40-char sample acestream ID
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add new route in the blueprint
@bp.route('/api/channels/check-status', methods=['POST'])
async def check_channels_status():
    """Check status of all active channels."""
    try:
        channel_repo = ChannelRepository()
        status_service = ChannelStatusService()
        
        # Get all active channels
        channels = channel_repo.get_active()
        
        # Check status of all channels
        results = await status_service.check_channels(channels)
        
        # Count online/offline channels
        online_count = sum(1 for r in results if r)
        
        return jsonify({
            'message': 'Channel status check completed',
            'total': len(channels),
            'online': online_count,
            'offline': len(channels) - online_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/config/ace_engine_url', methods=['PUT'])
def update_ace_engine_url():
    """Update the Ace Engine URL configuration."""
    try:
        data = request.get_json()
        new_url = data.get('ace_engine_url')
        
        if not new_url:
            return jsonify({'error': 'ace_engine_url is required'}), 400
            
        config = Config()
        config._config['ace_engine_url'] = new_url
        config._save_config()
        
        return jsonify({
            'message': 'Ace Engine URL updated successfully',
            'ace_engine_url': new_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/channels/<channel_id>/check-status', methods=['POST'])
async def check_channel_status(channel_id):
    """Check status of a specific channel."""
    try:
        channel_repo = ChannelRepository()
        status_service = ChannelStatusService()
        
        channel = channel_repo.get_by_id(channel_id)
        if not channel:
            return jsonify({'error': 'Channel not found'}), 404
        
        is_online = await status_service.check_channel(channel)
        
        return jsonify({
            'message': 'Channel status check completed',
            'channel_id': channel_id,
            'is_online': is_online,
            'last_checked': channel.last_checked.isoformat() if channel.last_checked else None,
            'error': channel.check_error
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/config/rescrape_interval', methods=['PUT'])
def update_rescrape_interval():
    """Update the URL rescraping interval."""
    try:
        data = request.get_json()
        hours = data.get('hours')
        
        if hours is None or not isinstance(hours, int) or hours < 1:
            return jsonify({'error': 'Valid rescrape interval in hours is required (minimum 1)'}), 400
            
        config = Config()
        config._config['rescrape_interval'] = hours
        config._save_config()
        
        return jsonify({
            'message': 'Rescrape interval updated successfully',
            'rescrape_interval_hours': hours
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/health')
def health():
    """Health check endpoint for Docker."""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        
        # Check Acexy if enabled
        if os.environ.get('ENABLE_ACEXY') == 'true':
            try:
                acexy_response = requests.get('http://localhost:8080/ace/status', timeout=2)
                if not acexy_response.ok:
                    current_app.logger.warning("Acexy health check failed")
            except Exception as e:
                current_app.logger.warning(f"Acexy health check failed: {str(e)}")
                # Don't fail the whole health check if just Acexy is down
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/config/acexy_status')
def acexy_status():
    """Return if Acexy is enabled and available."""
    enabled = os.environ.get('ENABLE_ACEXY') == 'true'
    available = False
    
    if enabled:
        try:
            response = requests.get('http://localhost:8080/ace/status', timeout=2)
            available = response.ok
        except Exception:  # Add explicit Exception
            available = False
    
    return jsonify({
        "enabled": enabled,
        "available": available
    })
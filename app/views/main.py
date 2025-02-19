from flask import Blueprint, render_template, jsonify, request, Response
from datetime import datetime, timedelta
import asyncio
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..utils.config import Config
from ..tasks.manager import TaskManager
from ..services import ScraperService, PlaylistService
from ..repositories import URLRepository

bp = Blueprint('main', __name__)

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
        'base_url': config.base_url  # Add this line
    })

@bp.route('/api/channels')
def get_channels():
    """Get all channels."""
    channels = AcestreamChannel.query.all()
    return jsonify([{
        'id': ch.id,
        'name': ch.name,
        'last_processed': ch.last_processed.isoformat() if ch.last_processed else None
    } for ch in channels])

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
    """Generate and return M3U playlist with optional refresh."""
    should_refresh = request.args.get('refresh', '').lower() == 'true'
    
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
    
    # Generate playlist using service
    playlist_service = PlaylistService()
    playlist = playlist_service.generate_playlist()
    
    return Response(
        playlist,
        mimetype='audio/x-mpegurl',
        headers={
            'Content-Disposition': f'attachment; filename=acestream_playlist_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.m3u'
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
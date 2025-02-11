from flask import Blueprint, render_template, jsonify, request, Response
from datetime import datetime
import asyncio
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..utils.config import Config
from ..tasks.manager import TaskManager

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@bp.route('/api/stats')
def get_stats():
    """Get scraping statistics."""
    urls = ScrapedURL.query.all()
    channels = AcestreamChannel.query.all()
    
    url_stats = []
    for url in urls:
        channel_count = AcestreamChannel.query.filter(
            AcestreamChannel.last_processed == url.last_processed
        ).count()
        
        url_stats.append({
            'url': url.url,
            'status': url.status,
            'last_processed': url.last_processed.isoformat() if url.last_processed else None,
            'channel_count': channel_count
        })
    
    return jsonify({
        'urls': url_stats,
        'total_channels': len(channels)
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
    
    # Add to config
    config = Config()
    if url not in config.urls:
        config.add_url(url)
    
    # Add to database
    url_record = ScrapedURL(url=url, status='pending')
    db.session.add(url_record)
    db.session.commit()
    
    return jsonify({'message': 'URL added successfully'})

@bp.route('/api/refresh', methods=['POST'])
async def refresh_urls():
    """Force refresh all URLs."""
    try:
        task_manager = TaskManager()
        await task_manager.process_urls()
        return jsonify({'message': 'Refresh completed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/playlist.m3u')
def get_playlist():
    """Generate and return M3U playlist."""
    channels = AcestreamChannel.query.all()
    
    # Start with M3U header
    playlist = ['#EXTM3U']
    
    # Add each channel
    for channel in channels:
        # Add extended info
        playlist.append(f'#EXTINF:-1,{channel.name}')
        # Add stream URL
        playlist.append(f'acestream://{channel.id}')
    
    # Join with newlines and return as a playlist file
    return Response(
        '\n'.join(playlist),
        mimetype='audio/x-mpegurl',
        headers={'Content-Disposition': f'attachment; filename=acestream_playlist_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.m3u'}
    )
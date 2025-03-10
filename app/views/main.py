from flask import Blueprint, render_template, jsonify, request, Response, current_app, redirect, url_for
from datetime import datetime, timedelta, timezone
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
    """Render the dashboard page."""
    config = Config()
    if not config.is_initialized() and not current_app.testing:
        return redirect(url_for('main.setup'))
    return render_template('dashboard.html')

@bp.route('/playlist.m3u')
def get_playlist():
    """
    Legacy endpoint for M3U playlist.
    Maintains backward compatibility by directly serving the playlist.
    """
    # Skip setup check in tests
    config = Config()
    if not config.is_initialized() and not current_app.testing:
        return redirect(url_for('main.setup'))
        
    # Get query parameters
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    search = request.args.get('search', None)
    
    # Refresh data if requested
    if refresh and task_manager:
        from app.repositories import URLRepository
        url_repository = URLRepository()
        urls = url_repository.get_enabled()
        
        # Queue all enabled URLs for processing
        for url in urls:
            task_manager.add_url(url.url)
    
    # Generate playlist using service
    playlist_service = PlaylistService()
    playlist = playlist_service.generate_playlist(search_term=search)
    
    # Generate filename with timestamp
    filename = f"acestream_playlist_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    if search:
        filename += f"_filtered"
    filename += ".m3u"
    
    # Return playlist as downloadable file
    return Response(
        playlist,
        mimetype="audio/x-mpegurl",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@bp.route('/config')
def config():
    """Render the configuration page."""
    return render_template('config.html')

@bp.route('/setup')
def setup():
    """Render the setup wizard."""
    # Check if config already exists
    config = Config()
    if config.is_initialized():
        return redirect(url_for('main.index'))
    return render_template('setup.html')
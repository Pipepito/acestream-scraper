from flask import Blueprint, render_template, jsonify, request, Response, current_app, redirect, url_for
from datetime import datetime, timedelta, timezone
import asyncio
import logging
import os
import requests
from sqlalchemy import text
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..utils.config import Config
from ..tasks.manager import TaskManager
from ..services import ScraperService, PlaylistService
from ..repositories import URLRepository, ChannelRepository
from ..services.channel_status_service import ChannelStatusService

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Add a reference to the task manager
task_manager = None

@bp.route('/')
def index():
    """Main dashboard view."""
    config = Config()
    
    # If config was imported from file, redirect to dashboard
    if config.settings_repo and config.settings_repo.is_setup_completed():
        return render_template('dashboard.html')
        
    # If no config imported, redirect to setup
    return redirect(url_for('main.setup'))

@bp.route('/dashboard')
def dashboard():
    """Alternative endpoint for dashboard."""
    return index()

@bp.route('/search')
def search():
    """Acestream search page."""
    config = Config()
    
    # If config was not imported, redirect to setup
    if not config.settings_repo or not config.settings_repo.is_setup_completed():
        return redirect(url_for('main.setup'))
        
    return render_template('search.html')

@bp.route('/playlist.m3u')
def get_playlist():
    """
    Legacy endpoint for M3U playlist.
    Maintains backward compatibility by directly serving the playlist.
    """
    config = Config()
    if not config.is_initialized() and not current_app.testing:
        return redirect(url_for('main.setup'))
        
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    search = request.args.get('search', None)
    base_url_param = request.args.get('base_url', None)
    
    if refresh and task_manager:
        from app.repositories import URLRepository
        url_repository = URLRepository()
        urls = url_repository.get_enabled()
        
        for url in urls:
            task_manager.add_url(url.url)
    
    playlist_service = PlaylistService()
    
    if base_url_param:
        original_base_url = playlist_service.config.base_url
        playlist_service.config.base_url = base_url_param
        playlist = playlist_service.generate_playlist(search_term=search)
        playlist_service.config.base_url = original_base_url
    else:
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

@bp.route('/config')
def config():
    """Render the configuration page."""
    return render_template('config.html')

@bp.route('/setup')
def setup():
    """Setup wizard view."""
    config = Config()
    if config.is_initialized():
        current_app.logger.info("Configuration already initialized, redirecting to dashboard")
        return redirect(url_for('main.index'))
    return render_template('setup.html')
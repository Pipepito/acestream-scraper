from flask import Blueprint, jsonify
from flask_restx import Api

bp = Blueprint('api', __name__)
api = Api(bp, 
    version='1.0', 
    title='Acestream Scraper API',
    description='REST API for Acestream channels and configurations',
    doc='/docs'
)

# Import and register namespaces AFTER creating the Api instance
from app.api.controllers.stats_controller import api as stats_ns
from app.api.controllers.config_controller import api as config_ns
from app.api.controllers.channels_controller import api as channels_ns
from app.api.controllers.urls_controller import api as urls_ns
from app.api.controllers.health_controller import api as health_ns
from app.api.controllers.playlist_controller import api as playlist_ns
from app.api.controllers.warp_controller import api as warp_ns
from app.api.controllers.search_controller import api as search_ns

# Add namespaces to the API
api.add_namespace(stats_ns, path='/stats')
api.add_namespace(config_ns, path='/config')
api.add_namespace(channels_ns, path='/channels')
api.add_namespace(urls_ns, path='/urls')
api.add_namespace(health_ns, path='/health')
api.add_namespace(playlist_ns, path='/playlists')
api.add_namespace(warp_ns, path='/warp')
api.add_namespace(search_ns, path='/search')

# Register the config routes with the config namespace
from . import config_routes
config_routes.register_routes(config_ns)

# Register error handlers
@bp.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404

@bp.errorhandler(500)
def handle_500(e):
    return jsonify({'error': 'Internal server error'}), 500
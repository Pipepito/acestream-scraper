from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, current_app
from app.models import ScrapedURL
from app.repositories import URLRepository, ChannelRepository
from datetime import datetime, timezone
from app.tasks.manager import TaskManager
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

task_manager = TaskManager()

if not hasattr(task_manager, 'add_task'):
    task_manager.add_task = lambda task_type, *args, **kwargs: None

api = Namespace('urls', description='URL management')

url_input_model = api.model('URLInput', {
    'url': fields.String(required=True, description='URL to scrape')
})

url_update_model = api.model('URLUpdate', {
    'enabled': fields.Boolean(description='Whether the URL is enabled')
})

url_model = api.model('URL', {
    'id': fields.String(description='Unique identifier for the URL'),
    'url': fields.String(description='URL being scraped'),
    'url_type': fields.String(description='Type of URL (regular, zeronet)'),
    'status': fields.String(description='Current status of the URL'),
    'last_scraped': fields.DateTime(description='When the URL was last processed'),
    'enabled': fields.Boolean(description='Whether the URL is enabled'),
    'error_count': fields.Integer(description='Number of consecutive errors'),
    'last_error': fields.String(description='Last error message, if any')
})

url_repo = URLRepository()
channel_repo = ChannelRepository()

@api.route('/')
class URLList(Resource):
    @api.doc('list_urls')
    @api.marshal_list_with(url_model)
    def get(self):
        """Get list of all URLs."""
        try:
            urls = ScrapedURL.query.all()
            return urls
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('create_url')
    @api.expect(url_input_model)
    @api.response(201, 'URL created and queued for processing')
    @api.response(409, 'URL already exists')
    @api.response(400, 'Invalid input')
    def post(self):
        """Add a new URL to scrape."""
        data = request.json
        
        try:
            # Check if URL is provided
            if 'url' not in data or not data['url'].strip():
                return {'error': 'URL is required'}, 400
                
            # Check if URL type is provided
            url_type = data.get('url_type')
            if not url_type or url_type == 'auto':
                return {'error': "URL type must be explicitly specified as 'regular' or 'zeronet'"}, 400
            
            # Check if URL type is valid
            if url_type not in ['regular', 'zeronet']:
                return {'error': f"Invalid URL type: {url_type}. Must be 'regular' or 'zeronet'"}, 400
            
            existing = url_repo.get_by_url(data['url'])
            if existing:
                api.abort(409, 'This URL already exists')
            
            # Create URL directly using repository method
            url_obj = url_repo.add(data['url'], url_type)
            
            try:
                task_manager.add_task('scrape_url', url_obj.url)
            except Exception as e:
                current_app.logger.error(f"Failed to queue URL for scraping: {e}")
            
            return {
                'message': 'URL added successfully and queued for processing',
                'url': url_obj.url,
                'url_type': url_obj.url_type
            }, 201
        except ValueError as ve:
            # Handle validation errors
            return {'error': str(ve)}, 400
        except Exception as e:
            api.abort(500, str(e))

@api.route('/<uuid:id>')
@api.param('id', 'The URL ID to manage')
class URLItem(Resource):
    @api.doc('get_url')
    @api.marshal_with(url_model)
    @api.response(404, 'URL not found')
    def get(self, id):
        """Get details for a specific URL by ID."""
        try:
            url_obj = url_repo.get_by_id(str(id))
            if not url_obj:
                api.abort(404, 'URL not found')
            
            return url_obj
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('update_url')
    @api.expect(url_update_model)
    @api.response(200, 'URL updated')
    @api.response(404, 'URL not found')
    def put(self, id):
        """Update a URL's properties by ID."""
        data = request.json
        
        try:
            url_obj = url_repo.get_by_id(str(id))
            if not url_obj:
                api.abort(404, 'URL not found')
            
            if 'enabled' in data:
                if data['enabled']:
                    url_obj.status = 'pending'
                else:
                    url_obj.status = 'disabled'
                url_obj.enabled = data['enabled']
                url_repo.update(url_obj)
            
            return {
                'message': 'URL updated successfully',
                'id': url_obj.id,
                'url': url_obj.url,
                'status': url_obj.status,
                'enabled': url_obj.enabled
            }
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('delete_url')
    @api.response(204, 'URL deleted')
    @api.response(404, 'URL not found')
    def delete(self, id):
        """Delete a URL and its associated channels by ID."""
        try:
            logger.debug(f"Attempting to delete URL with ID: {id}")
            
            url_obj = url_repo.get_by_id(str(id))
            if not url_obj:
                logger.warning(f"URL not found for deletion: ID {id}")
                api.abort(404, 'URL not found')
            
            # Store the URL for channel deletion
            url_to_delete = url_obj.url
            
            if not channel_repo.delete_by_source(url_to_delete):
                logger.error(f"Failed to delete associated channels for URL: {url_to_delete}")
            
            if url_repo.delete(url_obj):
                logger.info(f"Successfully deleted URL: {url_to_delete} (ID: {id})")
                return '', 204
            
            logger.error(f"Failed to delete URL: {url_to_delete} (ID: {id})")
            api.abort(500, "Failed to delete URL")
            
        except Exception as e:
            logger.error(f"Error deleting URL: {e}", exc_info=True)
            api.abort(500, str(e))

@api.route('/<uuid:id>/refresh')
@api.param('id', 'The URL ID to refresh')
class URLRefresh(Resource):
    @api.doc('refresh_url')
    @api.response(200, 'URL queued for refreshing')
    @api.response(404, 'URL not found')
    @api.response(400, 'URL is disabled')
    def post(self, id):
        """Queue a specific URL for refreshing by ID."""
        try:
            url_obj = url_repo.get_by_id(str(id))
            if not url_obj:
                api.abort(404, 'URL not found')
            
            if not url_obj.enabled:
                api.abort(400, 'URL is disabled and cannot be refreshed')
            
            task_manager.add_task('scrape_url', url_obj.url)
            
            return {
                'message': 'URL queued for refreshing',
                'id': url_obj.id,
                'url': url_obj.url
            }
        except Exception as e:
            api.abort(500, str(e))

# Keep the old path-based endpoints for backward compatibility
@api.route('/<path:url>/details')
@api.param('url', 'The URL string to manage')
class URLItemByUrl(Resource):
    @api.doc('get_url_by_url')
    @api.marshal_with(url_model)
    @api.response(404, 'URL not found')
    def get(self, url):
        """Get details for a specific URL (backward compatibility)."""
        try:
            decoded_url = unquote(url)
            url_obj = url_repo.get_by_url(decoded_url)
            if not url_obj:
                api.abort(404, 'URL not found')
            
            return url_obj
        except Exception as e:
            api.abort(500, str(e))

@api.route('/<path:url>/refresh')
@api.param('url', 'The URL to refresh')
class URLRefreshByUrl(Resource):
    @api.doc('refresh_url_by_url')
    @api.response(200, 'URL queued for refreshing')
    @api.response(404, 'URL not found')
    def post(self, url):
        """Queue a specific URL for refreshing (backward compatibility)."""
        try:
            decoded_url = unquote(url)
            url_obj = url_repo.get_by_url(decoded_url)
            if not url_obj:
                api.abort(404, 'URL not found')
            
            if not url_obj.enabled:
                api.abort(400, 'URL is disabled and cannot be refreshed')
            
            task_manager.add_task('scrape_url', decoded_url)
            
            return {
                'message': 'URL queued for refreshing',
                'id': url_obj.id,
                'url': decoded_url
            }
        except Exception as e:
            api.abort(500, str(e))
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
    'url': fields.String(description='URL being scraped'),
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
    def post(self):
        """Add a new URL to scrape."""
        data = request.json
        
        try:
            existing = url_repo.get_by_url(data['url'])
            if existing:
                api.abort(409, 'This URL already exists')
            
            url = ScrapedURL(
                url=data['url'],
                added_at=datetime.now(timezone.utc),
                status='pending',
                enabled=True
            )
            url_repo.add(url)
            
            try:
                task_manager.add_task('scrape_url', data['url'])
            except Exception as e:
                current_app.logger.error(f"Failed to queue URL for scraping: {e}")
            
            return {
                'message': 'URL added successfully and queued for processing',
                'url': url.url
            }, 201
        except Exception as e:
            api.abort(500, str(e))

@api.route('/<path:url>')
@api.param('url', 'The URL to manage')
class URLItem(Resource):
    @api.doc('get_url')
    @api.marshal_with(url_model)
    @api.response(404, 'URL not found')
    def get(self, url):
        """Get details for a specific URL."""
        try:
            url_obj = url_repo.get_by_url(url)
            if not url_obj:
                api.abort(404, 'URL not found')
            
            return url_obj
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('update_url')
    @api.expect(url_update_model)
    @api.response(200, 'URL updated')
    @api.response(404, 'URL not found')
    def put(self, url):
        """Update a URL's properties."""
        data = request.json
        
        try:
            url_obj = url_repo.get_by_url(url)
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
                'url': url_obj.url,
                'status': url_obj.status,
                'enabled': url_obj.enabled
            }
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('delete_url')
    @api.response(204, 'URL deleted')
    @api.response(404, 'URL not found')
    def delete(self, url):
        """Delete a URL and its associated channels."""
        try:
            decoded_url = unquote(url)
            logger.debug(f"Attempting to delete URL: {decoded_url}")
            
            url_obj = url_repo.get_by_url(decoded_url)
            if not url_obj:
                logger.warning(f"URL not found for deletion: {decoded_url}")
                api.abort(404, 'URL not found')
            
            if not channel_repo.delete_by_source(decoded_url):
                logger.error(f"Failed to delete associated channels for URL: {decoded_url}")
            
            if url_repo.delete(url_obj):
                logger.info(f"Successfully deleted URL: {decoded_url}")
                return '', 204
            
            logger.error(f"Failed to delete URL: {decoded_url}")
            api.abort(500, "Failed to delete URL")
            
        except Exception as e:
            logger.error(f"Error deleting URL: {e}", exc_info=True)
            api.abort(500, str(e))

@api.route('/refresh')
class URLBatchRefresh(Resource):
    @api.doc('refresh_all_urls')
    @api.response(200, 'URLs queued for refreshing')
    def post(self):
        """Queue all URLs for refreshing."""
        try:
            urls = ScrapedURL.query.filter_by(enabled=True).all()
            
            for url in urls:
                task_manager.add_task('scrape_url', url.url)
            
            return {
                'message': f'Refreshing {len(urls)} URLs',
                'urls': [url.url for url in urls]
            }
        except Exception as e:
            api.abort(500, str(e))

@api.route('/<path:url>/refresh')
@api.param('url', 'The URL to refresh')
class URLRefresh(Resource):
    @api.doc('refresh_url')
    @api.response(200, 'URL queued for refreshing')
    @api.response(404, 'URL not found')
    @api.response(400, 'URL is disabled')
    def post(self, url):
        """Queue a specific URL for refreshing."""
        try:
            url_obj = url_repo.get_by_url(url)
            if not url_obj:
                api.abort(404, 'URL not found')
            
            if not url_obj.enabled:
                api.abort(400, 'URL is disabled and cannot be refreshed')
            
            task_manager.add_task('scrape_url', url)
            
            return {
                'message': 'URL queued for refreshing',
                'url': url
            }
        except Exception as e:
            api.abort(500, str(e))
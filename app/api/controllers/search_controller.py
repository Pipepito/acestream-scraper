import logging
from flask import request
from flask_restx import Namespace, Resource, fields

from app.models.acestream_channel import AcestreamChannel
from app.repositories.channel_repository import ChannelRepository
from app.services.acestream_search_service import AcestreamSearchService

logger = logging.getLogger(__name__)

# Create namespace
api = Namespace('search', description='Acestream channel search operations')

# Define models for documentation
search_result_model = api.model('SearchResult', {
    'id': fields.String(description='Acestream channel ID'),
    'name': fields.String(description='Channel name'),
    'infohash': fields.String(description='Infohash of the channel'),
    'bitrate': fields.Integer(description='Channel bitrate'),
    'categories': fields.List(fields.String, description='Categories of the channel'),
    'url': fields.String(description='Acestream URL')
})

pagination_model = api.model('SearchPagination', {
    'page': fields.Integer(description='Current page number'),
    'page_size': fields.Integer(description='Results per page'),
    'total_results': fields.Integer(description='Total number of results'),
    'total_pages': fields.Integer(description='Total number of pages')
})

search_response_model = api.model('SearchResponse', {
    'success': fields.Boolean(description='Success status of the request'),
    'message': fields.String(description='Message describing the result'),
    'results': fields.List(fields.Nested(search_result_model), description='Search results'),
    'pagination': fields.Nested(pagination_model, description='Pagination information')
})

channel_model = api.model('Channel', {
    'id': fields.String(description='Acestream channel ID'),
    'name': fields.String(description='Channel name'),
    'status': fields.String(description='Channel status'),
    'added_on': fields.DateTime(description='When the channel was added'),
    'last_checked': fields.DateTime(description='When the channel status was last checked')
})

add_channel_request_model = api.model('AddChannelRequest', {
    'id': fields.String(required=True, description='Acestream channel ID'),
    'name': fields.String(required=True, description='Channel name')
})

add_multiple_request_model = api.model('AddMultipleRequest', {
    'channels': fields.List(fields.Nested(add_channel_request_model), required=True, description='List of channels to add')
})

add_channel_response_model = api.model('AddChannelResponse', {
    'success': fields.Boolean(description='Success status of the request'),
    'message': fields.String(description='Message describing the result'),
    'channel': fields.Nested(channel_model, description='Added channel information')
})

add_multiple_response_model = api.model('AddMultipleResponse', {
    'success': fields.Boolean(description='Success status of the request'),
    'message': fields.String(description='Message describing the result'),
    'added_channels': fields.List(fields.Nested(channel_model), description='Successfully added channels'),
    'existing_channels': fields.List(fields.Nested(channel_model), description='Channels that already existed')
})

@api.route('')
@api.param('query', 'Search query string (optional)')
@api.param('page', 'Page number (default: 1)')
@api.param('page_size', 'Results per page (default: 10)')
@api.param('category', 'Filter by category (optional)')
class Search(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = AcestreamSearchService()
        self.channel_repo = ChannelRepository()
        
    @api.doc('search_channels')
    @api.response(200, 'Success', search_response_model)
    @api.response(400, 'Bad request')
    @api.response(500, 'Server error')
    def get(self):
        """Search for Acestream channels via engine API"""
        try:
            # Extract query parameters
            query = request.args.get('query', '')
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 10))
            category = request.args.get('category', '')
            
            # Removed the check for empty query to make it optional
            
            # Perform search
            search_results = self.search_service.search(query, page, page_size, category)
            
            return search_results, 200 if search_results['success'] else 500
            
        except ValueError as e:
            logger.error(f"Invalid parameter in search request: {str(e)}")
            return {'success': False, 'message': f'Invalid parameters: {str(e)}'}, 400
        except Exception as e:
            logger.error(f"Error in search endpoint: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}, 500

@api.route('/add')
class AddChannel(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = AcestreamSearchService()
        self.channel_repo = ChannelRepository()
        from app.repositories import URLRepository
        self.url_repo = URLRepository()
        
    @api.doc('add_channel')
    @api.expect(add_channel_request_model)
    @api.response(201, 'Channel added', add_channel_response_model)
    @api.response(400, 'Bad request')
    @api.response(409, 'Channel already exists')
    @api.response(500, 'Server error')
    def post(self):
        """Add a channel from search results to the database"""
        try:
            data = request.get_json()
            
            if not data:
                return {'success': False, 'message': 'No data provided'}, 400
            
            channel_id = data.get('id')
            channel_name = data.get('name')
            
            if not channel_id:
                return {'success': False, 'message': 'Channel ID is required'}, 400
            
            if not channel_name:
                return {'success': False, 'message': 'Channel name is required'}, 400
            
            # Check if channel already exists
            existing_channel = self.channel_repo.get_by_id(channel_id)
            if existing_channel:
                return {
                    'success': False, 
                    'message': f'Channel with ID {channel_id} already exists',
                    'channel': existing_channel.to_dict()
                }, 409
            
            # Create or get the Acestream Search URL entry
            acestream_search_url = self.url_repo.get_or_create_by_type_and_url(
                url_type="search",
                url="Acestream Search",
                trigger_scrape=False  # This type shouldn't trigger a scrape
            )
            
            # Create new channel with the scraped_url_id
            new_channel = AcestreamChannel(
                id=channel_id, 
                name=channel_name, 
                source_url="Acestream Search",  # Keep descriptive source
                scraped_url_id=acestream_search_url.id  # Link to the scraped URL
            )
            
            self.channel_repo.add(new_channel)
            
            return {
                'success': True,
                'message': f'Channel {channel_name} added successfully',
                'channel': new_channel.to_dict()
            }, 201
            
        except Exception as e:
            logger.error(f"Error adding channel from search: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}, 500

@api.route('/add_multiple')
class AddMultipleChannels(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = AcestreamSearchService()
        self.channel_repo = ChannelRepository()
        from app.repositories import URLRepository
        self.url_repo = URLRepository()
        
    @api.doc('add_multiple_channels')
    @api.expect(add_multiple_request_model)
    @api.response(201, 'Channels added', add_multiple_response_model)
    @api.response(400, 'Bad request')
    @api.response(500, 'Server error')
    def post(self):
        """Add multiple channels from search results to the database"""
        try:
            data = request.get_json()
            
            if not data:
                return {'success': False, 'message': 'No data provided'}, 400
            
            channels = data.get('channels', [])
            
            if not channels or not isinstance(channels, list):
                return {'success': False, 'message': 'No channels provided or invalid format'}, 400
            
            # Create or get the Acestream Search URL entry
            acestream_search_url = self.url_repo.get_or_create_by_type_and_url(
                url_type="search",
                url="Acestream Search",
                trigger_scrape=False  # This type shouldn't trigger a scrape
            )
            
            added_channels = []
            existing_channels = []
            
            for channel_data in channels:
                channel_id = channel_data.get('id')
                channel_name = channel_data.get('name')
                
                if not channel_id or not channel_name:
                    continue
                
                # Check if channel already exists
                existing_channel = self.channel_repo.get_by_id(channel_id)
                if existing_channel:
                    existing_channels.append(existing_channel.to_dict())
                    continue
                
                # Create new channel with the scraped_url_id
                new_channel = AcestreamChannel(
                    id=channel_id, 
                    name=channel_name,
                    source_url="Acestream Search",  # Keep descriptive source
                    scraped_url_id=acestream_search_url.id  # Link to the scraped URL
                )
                
                self.channel_repo.add(new_channel)
                added_channels.append(new_channel.to_dict())
            
            return {
                'success': True,
                'message': f'Added {len(added_channels)} channels, {len(existing_channels)} already existed',
                'added_channels': added_channels,
                'existing_channels': existing_channels
            }, 201
            
        except Exception as e:
            logger.error(f"Error adding multiple channels from search: {str(e)}")
            return {'success': False, 'message': f'Server error: {str(e)}'}, 500
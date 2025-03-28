import asyncio
import logging
from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from app.models import AcestreamChannel
from app.repositories import ChannelRepository, URLRepository
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

api = Namespace('channels', description='Channel management')

channel_input_model = api.model('ChannelInput', {
    'id': fields.String(required=True, description='Acestream Channel ID'),
    'name': fields.String(required=True, description='Channel name')
})

channel_model = api.model('Channel', {
    'id': fields.String(description='Acestream Channel ID'),
    'name': fields.String(description='Channel name'),
    'status': fields.String(description='Channel status'),
    'last_processed': fields.DateTime(description='When the channel was last processed'),
    'is_online': fields.Boolean(description='Whether the channel is online'),
    'last_checked': fields.DateTime(description='When the channel status was last checked'),
    'check_error': fields.String(description='Error message from last check'),
    'group': fields.String(description='Channel group/category')
})

status_check_result_model = api.model('StatusCheckResult', {
    'id': fields.String(description='Acestream Channel ID'),
    'name': fields.String(description='Channel name'),
    'is_online': fields.Boolean(description='Whether the channel is online'),
    'status': fields.String(description='Channel status: online/offline'),
    'last_checked': fields.DateTime(description='When the channel status was checked'),
    'error': fields.String(description='Error message, if any')
})

# Updated parser to include URL ID filter parameter
channel_parser = reqparse.RequestParser()
channel_parser.add_argument('search', type=str, required=False, help='Filter channels by name')
channel_parser.add_argument('url_id', type=str, required=False, help='Filter channels by source URL ID')
channel_parser.add_argument('page', type=int, required=False, default=1, help='Page number')
channel_parser.add_argument('per_page', type=int, required=False, default=25, help='Items per page')
channel_parser.add_argument('status', type=str, required=False, help='Filter by status')

channel_repo = ChannelRepository()
url_repo = URLRepository()  # Add this URL repository instance

def handle_repository_error(e: Exception, operation: str):
    """Handle repository errors consistently."""
    logger.error(f"Error in channels controller - {operation}: {str(e)}")
    api.abort(500, f"Failed to {operation}: {str(e)}")

@api.route('/')
class ChannelList(Resource):
    @api.doc('list_channels')
    @api.expect(channel_parser)
    @api.marshal_list_with(channel_model)
    def get(self):
        """Get list of channels, optionally filtered by search term or source URL."""
        try:
            args = channel_parser.parse_args()
            search = args.get('search', '')
            url_id = args.get('url_id', '')
            
            # First get channels (either all or filtered by search term)
            channels = channel_repo.search(search) if search else channel_repo.get_active()
            
            # Then filter by URL ID if provided
            if url_id:
                url_obj = url_repo.get_by_id(url_id)
                
                if url_obj:
                    # Filter channels by source URL
                    channels = [ch for ch in channels if ch.source_url == url_obj.url]
                else:
                    # If URL ID not found, return empty list
                    channels = []
            
            return channels
        except Exception as e:
            handle_repository_error(e, "fetch channels")
    
    @api.doc('create_channel')
    @api.expect(channel_input_model)
    @api.response(201, 'Channel created')
    @api.response(409, 'Channel already exists')
    def post(self):
        """Add a new channel."""
        data = request.json
        try:
            channel = channel_repo.create(
                channel_id=data['id'],
                name=data['name']
            )
            if not channel:
                api.abort(500, "Failed to create channel")
            
            return {
                'message': 'Channel added successfully',
                'id': channel.id,
                'name': channel.name
            }, 201
        except Exception as e:
            api.abort(500, str(e))

@api.route('/<string:channel_id>')
@api.param('channel_id', 'The channel identifier')
class Channel(Resource):
    @api.doc('get_channel')
    @api.marshal_with(channel_model)
    @api.response(404, 'Channel not found')
    def get(self, channel_id):
        """Get details for a specific channel."""
        try:
            channel = channel_repo.get_by_id(channel_id)
            if not channel:
                api.abort(404, 'Channel not found')
            
            return channel
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('delete_channel')
    @api.response(200, 'Channel deleted')
    @api.response(404, 'Channel not found')
    def delete(self, channel_id):
        """Delete a channel."""
        try:
            if channel_repo.delete(channel_id):
                return {'message': 'Channel deleted successfully'}
            api.abort(404, 'Channel not found')
        except Exception as e:
            api.abort(500, str(e))

@api.route('/<string:channel_id>/check-status')
@api.param('channel_id', 'The channel identifier')
class ChannelStatusCheck(Resource):
    @api.doc('check_channel_status')
    @api.marshal_with(status_check_result_model)
    @api.response(404, 'Channel not found')
    def post(self, channel_id):
        """Check online status for a specific channel."""
        try:
            # Just verify the channel exists
            channel = channel_repo.get_by_id(channel_id)
            if not channel:
                api.abort(404, 'Channel not found')
            
            # Instead of passing the ORM object, just pass the ID
            from app.services.channel_status_service import check_channel_status
            
            # Pass only the channel ID to the async function
            result = asyncio.run(check_channel_status(channel_id))
            
            # Return the result - no need to access ORM object here
            return {
                'id': result['id'],
                'name': result['name'],
                'status': result['status'],
                'is_online': result['is_online'],
                'last_checked': result['last_checked'],
                'error': result.get('error', None)
            }
        except Exception as e:
            logger.error(f"Error checking channel status: {e}", exc_info=True)
            api.abort(500, str(e))

@api.route('/check-status')
class ChannelBatchStatusCheck(Resource):
    @api.doc('check_all_channels_status')
    @api.response(202, 'Status check initiated')
    def post(self):
        """Start background check for all channels."""
        try:
            from app.services.channel_status_service import start_background_check
            from app.repositories.channel_repository import ChannelRepository
            
            channel_repo = ChannelRepository()
            channels = channel_repo.get_all()
            
            if not channels:
                return {
                    'message': 'No channels to check',
                    'total_channels': 0
                }, 200
            
            # Start background check
            result = start_background_check(channels)
            
            return {
                'message': 'Channel status check initiated',
                'total_channels': result['total_channels']
            }, 202
            
        except Exception as e:
            logger.error(f"Error initiating status check: {e}", exc_info=True)
            return {
                'error': 'Failed to start status check',
                'message': str(e)
            }, 500

@api.route('/url/<string:url_id>/channels')
@api.param('url_id', 'The URL ID to filter channels by')
class ChannelsByUrlId(Resource):
    @api.doc('get_channels_by_url_id')
    @api.marshal_list_with(channel_model)
    @api.response(404, 'URL not found')
    def get(self, url_id):
        """Get channels for a specific URL ID."""
        try:
            url_obj = url_repo.get_by_id(url_id)
            if not url_obj:
                api.abort(404, 'URL not found')
            
            # Get channels for this URL
            channels = channel_repo.get_by_source(url_obj.url)
            return channels
        except Exception as e:
            handle_repository_error(e, "fetch channels by URL ID")
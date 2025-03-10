from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from app.models import AcestreamChannel
from app.repositories import ChannelRepository
from datetime import datetime, timezone

api = Namespace('channels', description='Channel management')

# Model definitions
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
    'check_error': fields.String(description='Error message from last check')
})

status_check_result_model = api.model('StatusCheckResult', {
    'id': fields.String(description='Acestream Channel ID'),
    'name': fields.String(description='Channel name'),
    'is_online': fields.Boolean(description='Whether the channel is online'),
    'last_checked': fields.DateTime(description='When the channel status was checked'),
    'error': fields.String(description='Error message, if any')
})

# Parser for query parameters
channel_parser = reqparse.RequestParser()
channel_parser.add_argument('search', type=str, required=False, help='Filter channels by name')

channel_repo = ChannelRepository()

@api.route('/')
class ChannelList(Resource):
    @api.doc('list_channels')
    @api.expect(channel_parser)
    @api.marshal_list_with(channel_model)
    def get(self):
        """Get list of channels, optionally filtered by search term."""
        args = channel_parser.parse_args()
        search = args.get('search', '')
        
        try:
            if (search):
                channels = AcestreamChannel.query.filter(
                    AcestreamChannel.name.ilike(f'%{search}%')
                ).all()
            else:
                channels = AcestreamChannel.query.all()
            
            return channels
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('create_channel')
    @api.expect(channel_input_model)
    @api.response(201, 'Channel created')
    @api.response(409, 'Channel already exists')
    def post(self):
        """Add a new channel."""
        data = request.json
        
        try:
            # Check if channel already exists
            existing = channel_repo.get_by_id(data['id'])
            if existing:
                api.abort(409, 'A channel with this ID already exists')
            
            # Create new channel
            channel = AcestreamChannel(
                id=data['id'],
                name=data['name'],
                status='active',
                added_at=datetime.now(timezone.utc)
            )
            channel_repo.add(channel)
            
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
            channel = channel_repo.get_by_id(channel_id)
            if not channel:
                api.abort(404, 'Channel not found')
            
            channel_repo.delete(channel)
            return {'message': 'Channel deleted successfully'}
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
            channel = channel_repo.get_by_id(channel_id)
            if not channel:
                api.abort(404, 'Channel not found')
            
            # Import here to avoid circular imports
            from app.services.channel_status_service import check_channel_status
            
            result = check_channel_status(channel)
            
            return {
                'id': channel.id,
                'name': channel.name,
                'is_online': result['is_online'],
                'last_checked': result['last_checked'],
                'error': result.get('error', None)
            }
        except Exception as e:
            api.abort(500, str(e))

@api.route('/check-status')
class ChannelBatchStatusCheck(Resource):
    @api.doc('check_all_channels_status')
    @api.response(200, 'Status check initiated')
    def post(self):
        """Check online status for all channels."""
        try:
            # Import here to avoid circular imports
            from app.services.channel_status_service import check_all_channels_status
            
            result = check_all_channels_status()
            
            return {
                'message': 'Channel status check completed',
                'online': result['online'],
                'offline': result['offline']
            }
        except Exception as e:
            api.abort(500, str(e))
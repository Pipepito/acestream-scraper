from flask import request
from flask_restx import Resource, Namespace, fields
from app.repositories.tv_channel_repository import TVChannelRepository
from app.services.tv_channel_service import TVChannelService
from app.repositories.channel_repository import ChannelRepository
from app.models.tv_channel import TVChannel
from app.models.acestream_channel import AcestreamChannel

api = Namespace('tv_channels', description='TV Channels operations')

# Models for request/response
tv_channel_model = api.model('TVChannel', {
    'id': fields.Integer(readonly=True, description='TV Channel ID'),
    'name': fields.String(required=True, description='Channel name'),
    'description': fields.String(description='Channel description'),
    'logo_url': fields.String(description='Logo URL'),
    'category': fields.String(description='Channel category'),
    'country': fields.String(description='Country of origin'),
    'language': fields.String(description='Primary language'),
    'website': fields.String(description='Official website URL'),
    'epg_id': fields.String(description='ID used for EPG mapping'),
    'epg_source_id': fields.Integer(description='EPG source ID'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp'),
    'is_active': fields.Boolean(description='Whether the channel is active'),
    'acestream_channels_count': fields.Integer(readonly=True, description='Count of associated acestreams')
})

tv_channel_create_model = api.model('TVChannelCreate', {
    'name': fields.String(required=True, description='Channel name'),
    'description': fields.String(description='Channel description'),
    'logo_url': fields.String(description='Logo URL'),
    'category': fields.String(description='Channel category'),
    'country': fields.String(description='Country of origin'),
    'language': fields.String(description='Primary language'),
    'website': fields.String(description='Official website URL'),
    'epg_id': fields.String(description='ID used for EPG mapping'),
    'epg_source_id': fields.Integer(description='EPG source ID'),
    'is_active': fields.Boolean(description='Whether the channel is active')
})

tv_channel_update_model = api.model('TVChannelUpdate', {
    'name': fields.String(description='Channel name'),
    'description': fields.String(description='Channel description'),
    'logo_url': fields.String(description='Logo URL'),
    'category': fields.String(description='Channel category'),
    'country': fields.String(description='Country of origin'),
    'language': fields.String(description='Primary language'),
    'website': fields.String(description='Official website URL'),
    'epg_id': fields.String(description='ID used for EPG mapping'),
    'epg_source_id': fields.Integer(description='EPG source ID'),
    'is_active': fields.Boolean(description='Whether the channel is active')
})

acestream_assign_model = api.model('AcestreamAssign', {
    'acestream_id': fields.String(required=True, description='Acestream channel ID')
})

batch_assign_model = api.model('BatchAssign', {
    'patterns': fields.Raw(required=True, description='Dictionary of patterns to TV channel IDs')
})

# Parse query parameters
parser = api.parser()
parser.add_argument('category', type=str, help='Filter by category')
parser.add_argument('country', type=str, help='Filter by country')
parser.add_argument('language', type=str, help='Filter by language')
parser.add_argument('search', type=str, help='Search term')
parser.add_argument('page', type=int, default=1, help='Page number')
parser.add_argument('per_page', type=int, default=20, help='Items per page')
parser.add_argument('is_active', type=bool, help='Filter by active status')

@api.route('/')
class TVChannelsResource(Resource):
    @api.doc('list_tv_channels')
    @api.expect(parser)
    def get(self):
        """List TV channels with optional filtering"""
        args = parser.parse_args()
        repo = TVChannelRepository()
        
        # Get filtered channels with pagination
        channels, total, total_pages = repo.filter_channels(
            category=args.get('category'),
            country=args.get('country'),
            language=args.get('language'),
            search_term=args.get('search'),
            page=args.get('page', 1),
            per_page=args.get('per_page', 20)
        )
        
        # Get unique filter options for dropdowns
        categories = repo.get_categories()
        countries = repo.get_countries()
        languages = repo.get_languages()
        
        return {
            'channels': [channel.to_dict() for channel in channels],
            'total': total,
            'page': args.get('page', 1),
            'per_page': args.get('per_page', 20),
            'total_pages': total_pages,
            'filters': {
                'categories': categories,
                'countries': countries,
                'languages': languages
            }
        }
    
    @api.doc('create_tv_channel')
    @api.expect(tv_channel_create_model)
    @api.response(201, 'TV Channel created successfully')
    def post(self):
        """Create a new TV channel"""
        repo = TVChannelRepository()
        data = request.json
        
        try:
            # Create the TV channel
            channel = repo.create(data)
            return {
                'message': 'TV Channel created successfully', 
                'id': channel.id,
                'channel': channel.to_dict()
            }, 201
        except Exception as e:
            api.abort(400, str(e))

@api.route('/<int:id>')
@api.param('id', 'The TV channel ID')
class TVChannelResource(Resource):
    @api.doc('get_tv_channel')
    @api.response(200, 'Success')
    @api.response(404, 'TV Channel not found')
    def get(self, id):
        """Get a TV channel by ID"""
        repo = TVChannelRepository()
        channel = repo.get_by_id(id)
        
        if not channel:
            api.abort(404, f'TV Channel {id} not found')
            
        # Get associated acestream channels
        acestreams = AcestreamChannel.query.filter_by(tv_channel_id=id).all()
        
        result = channel.to_dict()
        result['acestream_channels'] = [stream.to_dict() for stream in acestreams]
        
        return result
    
    @api.doc('update_tv_channel')
    @api.expect(tv_channel_update_model)
    @api.response(200, 'TV Channel updated successfully')
    @api.response(404, 'TV Channel not found')
    def put(self, id):
        """Update a TV channel"""
        repo = TVChannelRepository()
        data = request.json
        
        updated = repo.update(id, data)
        if not updated:
            api.abort(404, f'TV Channel {id} not found')
            
        return {
            'message': 'TV Channel updated successfully',
            'channel': updated.to_dict()
        }
    
    @api.doc('delete_tv_channel')
    @api.response(200, 'TV Channel deleted successfully')
    @api.response(404, 'TV Channel not found')
    def delete(self, id):
        """Delete a TV channel"""
        repo = TVChannelRepository()
        
        success = repo.delete(id)
        if not success:
            api.abort(404, f'TV Channel {id} not found')
            
        return {'message': f'TV Channel {id} deleted successfully'}

@api.route('/<int:id>/acestreams')
@api.param('id', 'The TV channel ID')
class TVChannelAcestreamsResource(Resource):
    @api.doc('get_acestreams')
    @api.response(200, 'Success')
    @api.response(404, 'TV Channel not found')
    def get(self, id):
        """Get acestream channels for a TV channel"""
        repo = TVChannelRepository()
        channel = repo.get_by_id(id)
        
        if not channel:
            api.abort(404, f'TV Channel {id} not found')
            
        # Get associated acestream channels
        acestreams = AcestreamChannel.query.filter_by(tv_channel_id=id).all()
        
        return {
            'channel_id': id,
            'channel_name': channel.name,
            'acestreams': [stream.to_dict() for stream in acestreams]
        }
    
    @api.doc('assign_acestream')
    @api.expect(acestream_assign_model)
    @api.response(201, 'Acestream assigned successfully')
    @api.response(404, 'TV Channel or Acestream not found')
    def post(self, id):
        """Assign an acestream channel to this TV channel"""
        repo = TVChannelRepository()
        data = request.json
        
        acestream_id = data.get('acestream_id')
        success = repo.assign_acestream(id, acestream_id)
        
        if not success:
            api.abort(404, f'TV Channel {id} or Acestream {acestream_id} not found')
            
        return {'message': f'Acestream {acestream_id} assigned to TV Channel {id}'}, 201

@api.route('/<int:id>/acestreams/<string:acestream_id>')
@api.param('id', 'The TV channel ID')
@api.param('acestream_id', 'The acestream channel ID')
class TVChannelAcestreamResource(Resource):
    @api.doc('remove_acestream')
    @api.response(200, 'Acestream removed successfully')
    @api.response(404, 'Association not found')
    def delete(self, id, acestream_id):
        """Remove an acestream channel from this TV channel"""
        repo = TVChannelRepository()
        
        success = repo.remove_acestream(id, acestream_id)
        if not success:
            api.abort(404, f'Association between TV Channel {id} and Acestream {acestream_id} not found')
            
        return {'message': f'Acestream {acestream_id} removed from TV Channel {id}'}

@api.route('/<int:id>/sync-epg')
@api.param('id', 'The TV channel ID')
class TVChannelEPGSyncResource(Resource):
    @api.doc('sync_epg')
    @api.response(200, 'EPG data synchronized')
    @api.response(404, 'TV Channel not found')
    def post(self, id):
        """Synchronize EPG data between TV channel and acestreams"""
        service = TVChannelService()
        repo = TVChannelRepository()
        
        # Check if channel exists
        channel = repo.get_by_id(id)
        if not channel:
            api.abort(404, f'TV Channel {id} not found')
        
        result = service.sync_epg_data(id)
        
        return {
            'message': 'EPG data synchronized',
            'changes_made': result
        }

@api.route('/batch-assign')
class BatchAssignResource(Resource):
    @api.doc('batch_assign')
    @api.expect(batch_assign_model)
    @api.response(200, 'Batch assignment complete')
    def post(self):
        """Batch assign acestreams to TV channels based on name patterns"""
        service = TVChannelService()
        data = request.json
        
        patterns = data.get('patterns', {})
        result = service.batch_assign_streams(patterns)
        
        return {
            'message': 'Batch assignment complete',
            'results': result
        }

@api.route('/associate-by-epg')
class AssociateByEPGResource(Resource):
    @api.doc('associate_by_epg')
    @api.response(200, 'EPG association complete')
    def post(self):
        """Associate acestreams with TV channels based on matching EPG IDs"""
        service = TVChannelService()
        result = service.associate_by_epg_id()
        
        return {
            'message': 'EPG association complete',
            'results': result
        }

@api.route('/bulk-update-epg')
class BulkUpdateEPGResource(Resource):
    @api.doc('bulk_update_epg')
    @api.response(200, 'Bulk EPG update complete')
    def post(self):
        """Update EPG data for all TV channels and their acestreams"""
        service = TVChannelService()
        result = service.bulk_update_epg()
        
        return {
            'message': 'Bulk EPG update complete',
            'stats': result
        }

@api.route('/unassigned-acestreams')
class UnassignedAcestreamsResource(Resource):
    @api.doc('get_unassigned')
    @api.expect(parser)
    def get(self):
        """Get acestreams not assigned to any TV channel with optional search filtering"""
        args = parser.parse_args()
        search_term = args.get('search', '')
        
        # Base query for unassigned acestreams
        query = AcestreamChannel.query.filter_by(tv_channel_id=None)
        
        # Add search filter if provided
        if search_term:
            query = query.filter(AcestreamChannel.name.ilike(f'%{search_term}%'))
        
        # Get the results
        acestreams = query.order_by(AcestreamChannel.name).limit(100).all()
        
        return {
            'total': len(acestreams),
            'acestreams': [stream.to_dict() for stream in acestreams]
        }

@api.route('/generate-from-acestreams')
class GenerateTVChannelsResource(Resource):
    @api.doc('generate_from_acestreams')
    @api.response(200, 'TV Channels generation complete')
    def post(self):
        """Generate TV channels from existing acestreams based on metadata"""
        service = TVChannelService()
        result = service.generate_tv_channels_from_acestreams()
        
        return {
            'message': 'TV Channels generation complete',
            'stats': result
        }

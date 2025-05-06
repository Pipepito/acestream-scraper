from flask import request
from flask_restx import Resource, Namespace, fields
from app.repositories.tv_channel_repository import TVChannelRepository
from app.services.tv_channel_service import TVChannelService
from app.repositories.channel_repository import ChannelRepository
from app.models.tv_channel import TVChannel
from app.models.acestream_channel import AcestreamChannel
from app.services.epg_service import EPGService
import logging

# Add logger
logger = logging.getLogger(__name__)

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
    'is_active': fields.Boolean(description='Whether the channel is active'),
    'selected_acestreams': fields.List(fields.String, description='List of acestream IDs to associate')
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

bulk_update_model = api.model('BulkUpdate', {
    'channel_ids': fields.List(fields.Integer, required=True, description='List of TV channel IDs to update'),
    'category': fields.String(description='Category to set for all channels'),
    'country': fields.String(description='Country to set for all channels'),
    'language': fields.String(description='Language to set for all channels'),
    'is_active': fields.Boolean(description='Active status to set for all channels')
})

# Add a new model for match results
match_result_model = api.model('MatchResult', {
    'epg_id': fields.String(description='EPG ID used for matching'),
    'name': fields.String(description='EPG channel name used for matching'),
    'matches': fields.List(fields.Nested(api.model('Match', {
        'channel': fields.Nested(tv_channel_model),
        'score': fields.Float(description='Match score (0-1)'),
        'match_type': fields.String(description='How the match was made (epg_id, name_similarity)')
    }))),
    'match_count': fields.Integer(description='Number of matches found')
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
parser.add_argument('favorites_only', type=bool, help='Show only favorite channels')

@api.route('/')
class TVChannelsList(Resource):
    @api.doc('list_tv_channels')
    @api.expect(parser)
    def get(self):
        """List TV channels with optional filtering"""
        args = parser.parse_args()
        category = args.get('category')
        country = args.get('country')
        language = args.get('language')
        search = args.get('search')
        page = args.get('page', 1)
        per_page = args.get('per_page', 20)
        favorites_only = args.get('favorites_only', False)
        
        try:
            # Create TV Channel repository instance
            repo = TVChannelRepository()
            
            # Use TV Channel repository to filter channels
            channels, total, total_pages = repo.filter_channels(
                category=category,
                country=country,
                language=language,
                search_term=search,
                page=page,
                per_page=per_page,
                favorites_only=favorites_only
            )
            
            # Convert to dictionaries for response
            channels_data = [c.to_dict() for c in channels]
            
            # Get all available filter options
            filters = {
                'categories': repo.get_categories(),
                'countries': repo.get_countries(),
                'languages': repo.get_languages()
            }
            
            # Return successful response with data
            response = {
                'channels': channels_data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'filters': filters
            }
            return response
        except Exception as e:
            api.abort(500, f"Error retrieving TV channels: {str(e)}")
    
    @api.doc('create_tv_channel')
    @api.expect(api.model('TVChannelCreate', {
        'name': fields.String(required=True, description='Channel name'),
        'description': fields.String(description='Channel description'),
        'logo_url': fields.String(description='Logo URL'),
        'category': fields.String(description='Channel category'),
        'country': fields.String(description='Country of origin'),
        'language': fields.String(description='Primary language'),
        'website': fields.String(description='Official website URL'),
        'epg_id': fields.String(description='ID used for EPG mapping'),
        'epg_source_id': fields.Integer(description='EPG source ID'),
        'is_active': fields.Boolean(description='Whether the channel is active'),
        'selected_acestreams': fields.List(fields.String, description='List of acestream IDs to associate')
    }))
    @api.response(201, 'TV Channel created successfully')
    def post(self):
        """Create a new TV channel"""
        repo = TVChannelRepository()
        data = request.json
        selected_acestreams = data.pop('selected_acestreams', []) if isinstance(data, dict) else []
        
        try:
            # Create the TV channel
            channel = repo.create(data)
            channel_id = channel.id
            
            # Associate selected acestreams if provided
            associated_count = 0
            if selected_acestreams and channel_id:
                for acestream_id in selected_acestreams:
                    if repo.assign_acestream(channel_id, acestream_id):
                        associated_count += 1
            
            return {
                'message': 'TV Channel created successfully', 
                'id': channel.id,
                'channel': channel.to_dict(),
                'associated_acestreams': associated_count
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

@api.route('/bulk-update')
class BulkUpdateResource(Resource):
    @api.doc('bulk_update_channels')
    @api.expect(bulk_update_model)
    @api.response(200, 'Channels updated successfully')
    @api.response(400, 'Invalid request')
    def post(self):
        """Bulk update multiple TV channels at once"""
        data = request.json
        channel_ids = data.get('channel_ids', [])
        
        if not channel_ids:
            api.abort(400, "No channel IDs provided")
            
        # Extract fields to update
        update_data = {}
        for field in ['category', 'country', 'language', 'is_active']:
            if field in data:
                update_data[field] = data[field]
                
        if not update_data:
            api.abort(400, "No fields provided for update")
            
        try:
            # Use the repository instead of direct DB access
            repo = TVChannelRepository()
            result = repo.bulk_update(channel_ids, update_data)
            return result
            
        except Exception as e:
            api.abort(500, f"Error updating channels: {str(e)}")

@api.route('/bulk-delete')
class BulkDeleteResource(Resource):
    @api.doc('bulk_delete_channels')
    @api.expect(api.model('BulkDelete', {
        'channel_ids': fields.List(fields.Integer, required=True, description='List of TV channel IDs to delete')
    }))
    @api.response(200, 'Channels deleted successfully')
    @api.response(400, 'Invalid request')
    def post(self):
        """Delete multiple TV channels at once"""
        data = request.json
        channel_ids = data.get('channel_ids', [])
        
        if not channel_ids:
            api.abort(400, "No channel IDs provided")
            
        try:
            # Create repository instance
            repo = TVChannelRepository()
            
            # Track successful deletions
            deleted_count = 0
            
            # Delete each channel
            for channel_id in channel_ids:
                if repo.delete(channel_id):
                    deleted_count += 1
            
            return {
                'message': f'Successfully deleted {deleted_count} channels',
                'deleted_count': deleted_count,
                'total_requested': len(channel_ids)
            }
            
        except Exception as e:
            api.abort(500, f"Error deleting channels: {str(e)}")

@api.route('/find-matches')
class FindMatchesResource(Resource):
    @api.doc('find_matching_acestreams')
    @api.param('epg_id', 'EPG Channel ID to match')
    @api.param('name', 'Channel name to match')
    @api.param('threshold', 'Similarity threshold (0-1)')
    @api.response(200, 'Found matches', match_result_model)
    def get(self):
        """Find acestream channels that match an EPG channel by ID or name"""
        epg_id = request.args.get('epg_id')
        name = request.args.get('name')
        
        # Get threshold from request, default to 0.3 if not provided
        try:
            threshold = float(request.args.get('threshold', 0.3))
            # Ensure threshold is within valid range
            threshold = max(0.1, min(threshold, 0.95))
        except (ValueError, TypeError):
            threshold = 0.3
        
        if not epg_id and not name:
            api.abort(400, "Either EPG ID or name is required for matching")
        
        try:
            # Initialize services and repositories
            epg_service = EPGService()
            channel_repo = ChannelRepository()
            
            # Get all acestream channels
            acestream_channels = channel_repo.get_all()
            
            # Create a simplified EPG channel for matching
            epg_channel = {'id': epg_id, 'name': name or epg_id}
            
            # Use the existing find_matching_channels function from EPGService
            # with apply_changes=False to just get matches without saving
            result = epg_service.find_matching_channels(
                [epg_channel],  # Pass as a list since the function expects a list
                acestream_channels,
                threshold=threshold,  # Use the provided threshold
                apply_changes=False  # Don't apply changes, just return matches
            )
            
            # Format the response
            matches = []
            if 'matches' in result:
                for match_item in result['matches']:
                    try:
                        # Fix the extraction of channel and score based on the actual structure
                        if isinstance(match_item, dict) and 'channel' in match_item:
                            channel = match_item['channel']
                            score = match_item.get('similarity', 0.0)
                            match_type = match_item.get('match_method', 'name_similarity')
                        elif isinstance(match_item, tuple) or isinstance(match_item, list):
                            # Handle tuple/list structure (channel, score)
                            channel = match_item[0]
                            score = match_item[1] if len(match_item) > 1 else 0.0
                            match_type = 'name_similarity'
                        else:
                            # Skip items with unknown structure
                            logger.warning(f"Skipping match item with unknown structure: {match_item}")
                            continue
                        
                        # Add to matches list
                        matches.append({
                            'channel': channel.to_dict() if hasattr(channel, 'to_dict') else channel,
                            'score': score,
                            'match_type': match_type
                        })
                    except (KeyError, IndexError, AttributeError) as e:
                        # Log the error but continue with other matches
                        logger.warning(f"Error processing match item: {e}, item: {match_item}")
                        continue
            
            # Sort matches by score descending
            matches.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'epg_id': epg_id,
                'name': name,
                'threshold': threshold,
                'matches': matches,
                'match_count': len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error finding matches: {e}", exc_info=True)
            api.abort(500, f"Error finding matches: {str(e)}")

@api.route('/favorites')
class TVChannelFavoritesResource(Resource):
    @api.doc('get_favorites')
    @api.response(200, 'Success')
    def get(self):
        """Get all favorite TV channels"""
        repo = TVChannelRepository()
        favorites = repo.get_favorites()
        
        return {
            'total': len(favorites),
            'favorites': [channel.to_dict() for channel in favorites]
        }

@api.route('/<int:id>/favorite')
@api.param('id', 'The TV channel ID')
class TVChannelFavoriteResource(Resource):
    @api.doc('set_favorite')
    @api.expect(api.model('SetFavorite', {
        'is_favorite': fields.Boolean(required=True, description='Favorite status to set')
    }))
    @api.response(200, 'Favorite status updated')
    @api.response(404, 'TV Channel not found')
    def post(self, id):
        """Set or unset a TV channel as favorite"""
        repo = TVChannelRepository()
        data = request.json
        
        is_favorite = data.get('is_favorite', True)
        channel = repo.set_favorite(id, is_favorite)
        
        if not channel:
            api.abort(404, f'TV Channel {id} not found')
            
        return {
            'message': f'TV Channel {id} {"marked as favorite" if is_favorite else "removed from favorites"}',
            'channel': channel.to_dict()
        }
        
    @api.doc('toggle_favorite')
    @api.response(200, 'Favorite status toggled')
    @api.response(404, 'TV Channel not found')
    def put(self, id):
        """Toggle favorite status of a TV channel"""
        repo = TVChannelRepository()
        
        result = repo.toggle_favorite(id)
        if not result:
            api.abort(404, f'TV Channel {id} not found')
            
        return {
            'message': f'TV Channel {id} {"marked as favorite" if result["is_favorite"] else "removed from favorites"}',
            'channel': result['channel'],
            'is_favorite': result['is_favorite']
        }

@api.route('/<int:id>/channel-number')
@api.param('id', 'The TV channel ID')
class TVChannelNumberResource(Resource):
    @api.doc('set_channel_number')
    @api.expect(api.model('SetChannelNumber', {
        'channel_number': fields.Integer(required=True, description='Channel number to set')
    }))
    @api.response(200, 'Channel number updated')
    @api.response(404, 'TV Channel not found')
    def post(self, id):
        """Set a channel number for a TV channel"""
        repo = TVChannelRepository()
        data = request.json
        
        channel_number = data.get('channel_number')
        if channel_number is None:
            api.abort(400, 'Channel number is required')
        
        channel = repo.set_channel_number(id, channel_number)
        
        if not channel:
            api.abort(404, f'TV Channel {id} not found')
            
        return {
            'message': f'Channel number for TV Channel {id} set to {channel_number}',
            'channel': channel.to_dict()
        }

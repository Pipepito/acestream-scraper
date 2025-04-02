from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
import logging

from app.models.epg_source import EPGSource
from app.models.epg_string_mapping import EPGStringMapping
from app.repositories.epg_source_repository import EPGSourceRepository
from app.repositories.epg_string_mapping_repository import EPGStringMappingRepository
from app.services.epg_service import EPGService

logger = logging.getLogger(__name__)

api = Namespace('epg', description='EPG configuration and management')

# Models for API documentation
epg_source_model = api.model('EPGSource', {
    'id': fields.Integer(readonly=True, description='Unique ID for the source'),
    'url': fields.String(required=True, description='URL of the EPG source (XMLTV)'),
    'enabled': fields.Boolean(default=True, description='Whether this source is enabled'),
    'last_updated': fields.DateTime(readonly=True, description='Last update timestamp'),
    'error_count': fields.Integer(readonly=True, description='Error counter'),
    'last_error': fields.String(readonly=True, description='Last error message')
})

epg_string_mapping_model = api.model('EPGStringMapping', {
    'id': fields.Integer(readonly=True, description='Unique ID for the mapping'),
    'search_pattern': fields.String(required=True, description='Text pattern to search in channel names'),
    'epg_channel_id': fields.String(required=True, description='EPG channel ID to map to')
})

# Auto-scan model including threshold and processing options
auto_scan_model = api.model('AutoScan', {
    'threshold': fields.Float(required=False, description='Similarity threshold (0.0-1.0)', default=0.8),
    'clean_unmatched': fields.Boolean(required=False, description='Clean EPG data if no match is found', default=False),
    'respect_existing': fields.Boolean(required=False, description='Don\'t modify channels that already have EPG data', default=False)
})

# Update options model for EPG channel updates
update_channels_model = api.model('UpdateChannels', {
    'respect_existing': fields.Boolean(required=False, description='Don\'t modify channels that already have EPG data', default=False),
    'clean_unmatched': fields.Boolean(required=False, description='Clean EPG data if no match is found', default=False)
})

# Endpoints for EPG sources
@api.route('/sources')
class EPGSourceListResource(Resource):
    @api.marshal_with(epg_source_model)
    def get(self):
        """Get all EPG sources"""
        repo = EPGSourceRepository()
        return repo.get_all()
    
    @api.expect(epg_source_model)
    @api.marshal_with(epg_source_model, code=201)
    def post(self):
        """Add a new EPG source"""
        data = request.json
        repo = EPGSourceRepository()
        
        # Validate URL presence
        url = data.get('url', '').strip()
        if not url:
            api.abort(400, "URL is required")
        
        # Validate URL format
        import re
        url_pattern = re.compile(r'^https?://\S+\.\S+')
        if not url_pattern.match(url):
            api.abort(400, "Invalid URL format. Must start with http:// or https://")
        
        # Check for duplicate sources
        existing_sources = repo.get_all()
        for source in existing_sources:
            if source.url.lower() == url.lower():
                api.abort(409, "This EPG source URL already exists")
        
        # Create new source
        source = EPGSource(
            url=url,
            enabled=data.get('enabled', True)
        )
        
        repo.create(source)
        return source, 201

@api.route('/sources/<int:id>')
class EPGSourceResource(Resource):
    def delete(self, id):
        """Delete EPG source"""
        repo = EPGSourceRepository()
        source = repo.get_by_id(id)
        if not source:
            api.abort(404, f"EPG source with ID {id} not found")
        
        repo.delete(source)
        return {'message': f'EPG source {id} deleted'}, 200

    @api.doc('update_epg_source')
    @api.expect(api.model('EPGSourceUpdate', {
        'enabled': fields.Boolean(required=False, description='Whether this source is enabled')
    }))
    @api.marshal_with(epg_source_model)
    def put(self, id):
        """Update an EPG source's enabled status"""
        repo = EPGSourceRepository()
        source = repo.get_by_id(id)
        if not source:
            api.abort(404, f"EPG source with ID {id} not found")
        
        data = request.json
        
        # Only allow updating the enabled flag
        if 'enabled' in data:
            source.enabled = data['enabled']
            
        repo.update(source)
        return source

# Endpoints for pattern mappings
@api.route('/mappings')
class EPGStringMappingListResource(Resource):
    @api.marshal_list_with(epg_string_mapping_model)
    def get(self):
        """Get all pattern mappings"""
        repo = EPGStringMappingRepository()
        return repo.get_all()
    
    @api.expect(epg_string_mapping_model)
    @api.marshal_with(epg_string_mapping_model, code=201)
    def post(self):
        """Add a new pattern mapping"""
        data = request.json
        repo = EPGStringMappingRepository()
        
        # Create new mapping from request data
        mapping = EPGStringMapping(
            search_pattern=data.get('search_pattern'),
            epg_channel_id=data.get('epg_channel_id')
        )
        
        repo.create(mapping)
        return mapping, 201

@api.route('/mappings/<int:id>')
class EPGStringMappingResource(Resource):
    def delete(self, id):
        """Delete pattern mapping"""
        repo = EPGStringMappingRepository()
        mapping = repo.get_by_id(id)
        if not mapping:
            api.abort(404, f"Mapping with ID {id} not found")
        
        repo.delete(mapping)
        return {'message': f'Mapping {id} deleted'}, 200

# Endpoints for EPG operations
@api.route('/refresh')
class EPGRefreshResource(Resource):
    def post(self):
        """Refresh EPG data from all sources"""
        service = EPGService()
        data = service.fetch_epg_data()
        return {
            'message': 'EPG data refreshed successfully',
            'channels_found': len(data)
        }

@api.route('/update-channels')
class EPGUpdateChannelsResource(Resource):
    @api.doc('update_epg_channels')
    @api.expect(update_channels_model)
    def post(self):
        """Update all channels with EPG metadata"""
        try:
            data = request.get_json() or {}
            respect_existing = data.get('respect_existing', False)
            clean_unmatched = data.get('clean_unmatched', False)
            
            service = EPGService()
            stats = service.update_all_channels_epg(
                respect_existing=respect_existing,
                clean_unmatched=clean_unmatched
            )
            
            return {
                'message': 'Channel EPG update process completed',
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Error updating channels with EPG data: {str(e)}")
            return {'error': str(e)}, 500

@api.route('/channels')
class EPGChannelsResource(Resource):
    def get(self):
        """Get all available EPG channel IDs and names"""
        service = EPGService()
        channels = []
        
        # Load EPG data if not already loaded
        if not service.epg_data:
            service.fetch_epg_data()
        
        # Convert to simple list of channel IDs and names
        for channel_id, data in service.epg_data.items():
            channels.append({
                'id': channel_id,
                'name': data.get('tvg_name', channel_id)
            })
        
        return channels

@api.route('/auto-scan')
class EPGAutoScanResource(Resource):
    @api.doc('auto_scan_epg')
    @api.expect(auto_scan_model)
    @api.response(200, 'Scan completed')
    def post(self):
        """Scan channels and automatically map EPG data based on name similarity."""
        try:
            data = request.get_json() or {}
            threshold = data.get('threshold', 0.8)
            clean_unmatched = data.get('clean_unmatched', False)
            respect_existing = data.get('respect_existing', False)
            
            service = EPGService()
            result = service.auto_scan_channels(
                threshold=threshold,
                clean_unmatched=clean_unmatched,
                respect_existing=respect_existing
            )
            
            return {
                'message': 'EPG auto-scan completed successfully',
                'total': result.get('total', 0),
                'matched': result.get('matched', 0),
                'cleaned': result.get('cleaned', 0),
                'skipped': result.get('skipped', 0)
            }
        except Exception as e:
            logger.error(f"Error during auto-scan: {str(e)}")
            return {'error': str(e)}, 500
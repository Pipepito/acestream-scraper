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
    'name': fields.String(description='Descriptive name for the source'),
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

# Endpoints for EPG sources
@api.route('/sources')
class EPGSourceListResource(Resource):
    @api.marshal_list_with(epg_source_model)
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
        
        # Create new source
        source = EPGSource(
            url=data.get('url'),
            name=data.get('name'),
            enabled=data.get('enabled', True)
        )
        
        repo.create(source)
        return source, 201

@api.route('/sources/<int:id>')
class EPGSourceResource(Resource):
    @api.marshal_with(epg_source_model)
    def get(self, id):
        """Get EPG source by ID"""
        repo = EPGSourceRepository()
        source = repo.get_by_id(id)
        if not source:
            api.abort(404, f"EPG source with ID {id} not found")
        return source
    
    @api.expect(epg_source_model)
    @api.marshal_with(epg_source_model)
    def put(self, id):
        """Update EPG source"""
        data = request.json
        repo = EPGSourceRepository()
        
        source = repo.get_by_id(id)
        if not source:
            api.abort(404, f"EPG source with ID {id} not found")
        
        if 'url' in data:
            source.url = data['url']
        if 'name' in data:
            source.name = data['name']
        if 'enabled' in data:
            source.enabled = data['enabled']
        
        repo.update(source)
        return source
    
    def delete(self, id):
        """Delete EPG source"""
        repo = EPGSourceRepository()
        source = repo.get_by_id(id)
        if not source:
            api.abort(404, f"EPG source with ID {id} not found")
        
        repo.delete(source)
        return {'message': f'EPG source {id} deleted'}, 200

@api.route('/sources/<int:id>/toggle')
class EPGSourceToggleResource(Resource):
    @api.marshal_with(epg_source_model)
    def post(self, id):
        """Toggle enabled status for an EPG source"""
        repo = EPGSourceRepository()
        source = repo.get_by_id(id)
        if not source:
            api.abort(404, f"EPG source with ID {id} not found")
        
        repo.toggle_enabled(source)
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
        
        # Create new mapping
        mapping = EPGStringMapping(
            search_pattern=data.get('search_pattern'),
            epg_channel_id=data.get('epg_channel_id')
        )
        
        repo.create(mapping)
        return mapping, 201

@api.route('/mappings/<int:id>')
class EPGStringMappingResource(Resource):
    @api.marshal_with(epg_string_mapping_model)
    def get(self, id):
        """Get pattern mapping by ID"""
        repo = EPGStringMappingRepository()
        mapping = repo.get_by_id(id)
        if not mapping:
            api.abort(404, f"Mapping with ID {id} not found")
        return mapping
    
    @api.expect(epg_string_mapping_model)
    @api.marshal_with(epg_string_mapping_model)
    def put(self, id):
        """Update pattern mapping"""
        data = request.json
        repo = EPGStringMappingRepository()
        
        mapping = repo.get_by_id(id)
        if not mapping:
            api.abort(404, f"Mapping with ID {id} not found")
        
        if 'search_pattern' in data:
            mapping.search_pattern = data['search_pattern']
        if 'epg_channel_id' in data:
            mapping.epg_channel_id = data['epg_channel_id']
        
        repo.update(mapping)
        return mapping
    
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
    def post(self):
        """Update all channels with EPG metadata"""
        service = EPGService()
        stats = service.update_all_channels()
        return {
            'message': 'Channel EPG update process completed',
            'stats': stats
        }
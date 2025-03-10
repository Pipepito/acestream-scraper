from flask_restx import Namespace, Resource, fields
from flask import request
import os
import requests
# Fix the import path - this is the key change
from app.repositories import SettingsRepository
from app.utils.config import Config
from app.extensions import db

api = Namespace('config', description='Configuration management')

# Model for updating base URL
base_url_model = api.model('BaseURL', {
    'base_url': fields.String(required=True, description='Base URL for acestream links')
})

# Model for updating Ace Engine URL
ace_engine_url_model = api.model('AceEngineURL', {
    'ace_engine_url': fields.String(required=True, description='URL for Acestream Engine')
})

# Model for updating rescrape interval
rescrape_interval_model = api.model('RescrapeInterval', {
    'hours': fields.Integer(required=True, description='Hours between automatic rescans')
})

# Model for Acexy status
acexy_status_model = api.model('AcexyStatus', {
    'enabled': fields.Boolean(description='Whether Acexy is enabled'),
    'available': fields.Boolean(description='Whether Acexy is available'),
    'message': fields.String(description='Status message')
})

@api.route('/base_url')
class BaseURL(Resource):
    @api.doc('update_base_url')
    @api.expect(base_url_model)
    def put(self):
        """Update base URL for acestream links."""
        data = request.json
        base_url = data.get('base_url')
        
        if not base_url:
            api.abort(400, "base_url is required")
        
        try:
            config = Config()
            config.base_url = base_url
            return {"message": "Base URL updated successfully"}
        except Exception as e:
            api.abort(500, str(e))

@api.route('/ace_engine_url')
class AceEngineURL(Resource):
    @api.doc('update_ace_engine_url')
    @api.expect(ace_engine_url_model)
    def put(self):
        """Update Acestream Engine URL."""
        data = request.json
        ace_engine_url = data.get('ace_engine_url')
        
        if not ace_engine_url:
            api.abort(400, "ace_engine_url is required")
        
        try:
            config = Config()
            config.ace_engine_url = ace_engine_url
            return {"message": "Ace Engine URL updated successfully"}
        except Exception as e:
            api.abort(500, str(e))

@api.route('/rescrape_interval')
class RescrapeInterval(Resource):
    @api.doc('get_rescrape_interval')
    def get(self):
        """Get current URL rescrape interval."""
        try:
            config = Config()
            return {"hours": config.rescrape_interval}
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('update_rescrape_interval')
    @api.expect(rescrape_interval_model)
    def put(self):
        """Update URL rescrape interval."""
        data = request.json
        hours = data.get('hours')
        
        if not hours:
            api.abort(400, "hours is required")
        
        try:
            config = Config()
            config.rescrape_interval = int(hours)
            return {"message": "Rescrape interval updated successfully"}
        except Exception as e:
            api.abort(500, str(e))

@api.route('/acexy_status')
class AcexyStatus(Resource):
    @api.doc('get_acexy_status')
    @api.marshal_with(acexy_status_model)
    def get(self):
        """Get Acexy status."""
        config = Config()
        
        # Check if Acexy is enabled via environment variable
        enabled = os.environ.get('ENABLE_ACEXY', 'false').lower() == 'true'
        
        if not enabled:
            return {
                "enabled": False,
                "available": False,
                "message": "Acexy is not enabled in this environment"
            }
        
        # Check if we can reach the Acexy service
        try:
            # Try to connect to Acexy status endpoint
            acexy_url = "http://localhost:8080/ace/status"
            response = requests.get(acexy_url, timeout=2)
            return {
                "enabled": True,
                "available": response.status_code == 200,
                "message": "Acexy is available" if response.status_code == 200 else "Acexy is not responding"
            }
        except:
            return {
                "enabled": True,
                "available": False,
                "message": "Could not connect to Acexy service"
            }

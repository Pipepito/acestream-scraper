from flask_restx import Namespace, Resource, fields
from flask import request
import os
import requests
from app.repositories import SettingsRepository
from app.utils.config import Config
from app.extensions import db
import logging
from app.services.acestream_status_service import AcestreamStatusService

logger = logging.getLogger(__name__)

api = Namespace('config', description='Configuration management')

base_url_model = api.model('BaseURL', {
    'base_url': fields.String(required=True, description='Base URL for acestream links')
})

addpid_model = api.model('AddPid', {
    'addpid': fields.Boolean(required=True, description='Whether to add PID parameter to URLs')
})

ace_engine_url_model = api.model('AceEngineURL', {
    'ace_engine_url': fields.String(required=True, description='URL for Acestream Engine')
})

rescrape_interval_model = api.model('RescrapeInterval', {
    'hours': fields.Integer(required=True, description='Hours between automatic rescans')
})

acexy_status_model = api.model('AcexyStatus', {
    'enabled': fields.Boolean(description='Whether Acexy is enabled'),
    'available': fields.Boolean(description='Whether Acexy is available'),
    'message': fields.String(description='Status message'),
    'active_streams': fields.Integer(description='Number of active streams')
})

acestream_status_model = api.model('AcestreamStatus', {
    'enabled': fields.Boolean(description='Whether Acestream Engine is enabled'),
    'available': fields.Boolean(description='Whether Acestream Engine is available'),
    'message': fields.String(description='Status message'),
    'version': fields.String(description='Acestream Engine version'),
    'platform': fields.String(description='Platform'),
    'playlist_loaded': fields.Boolean(description='Whether playlist is loaded'),
    'connected': fields.Boolean(description='Whether engine is connected to network')
})

status_check_interval_model = api.model('StatusCheckInterval', {
    'interval': fields.Integer(required=True, description='Check interval in seconds')
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
        
        enabled = os.environ.get('ENABLE_ACEXY', 'false').lower() == 'true'
        
        if not enabled:
            return {
                "enabled": False,
                "available": False,
                "message": "Acexy is not enabled in this environment",
                "active_streams": 0
            }
        
        try:
            # Get port from ACEXY_LISTEN_ADDR or default to 8080
            acexy_addr = os.environ.get('ACEXY_LISTEN_ADDR', ':8080')
            # If the address starts with a colon, it's just a port
            if acexy_addr.startswith(':'):
                acexy_port = acexy_addr[1:]  # Remove the colon
                acexy_url = f"http://localhost:{acexy_port}/ace/status"
            else:
                acexy_url = f"http://localhost{acexy_addr}/ace/status"
            
            response = requests.get(acexy_url, timeout=2)
            
            if response.status_code == 200:
                try:
                    # Try to parse as JSON first
                    data = response.json()
                    active_streams = data.get('streams', 0)
                except ValueError:
                    # If not valid JSON, try to parse as plain int
                    try:
                        active_streams = int(response.text)
                    except ValueError:
                        logger.warning(f"Could not parse Acexy response: {response.text}")
                        active_streams = 0
                
                return {
                    "enabled": True,
                    "available": True,
                    "message": f"Acexy is available ({active_streams} active streams)",
                    "active_streams": active_streams
                }
            return {
                "enabled": True,
                "available": False,
                "message": f"Acexy is not responding properly (HTTP {response.status_code})",
                "active_streams": 0
            }
        except Exception as e:
            logger.error(f"Error connecting to Acexy service: {str(e)}")
            return {
                "enabled": True,
                "available": False,
                "message": "Could not connect to Acexy service",
                "active_streams": 0
            }

@api.route('/setup_completed')
class SetupCompleted(Resource):
    @api.doc('mark_setup_completed')
    @api.expect(api.model('SetupCompleted', {
        'completed': fields.Boolean(required=True, description='Setup completion status')
    }))
    @api.response(200, 'Setup status updated')
    def put(self):
        """Mark setup as completed."""
        try:
            data = request.json
            config = Config()
            
            if data.get('completed'):
                config.settings_repo.mark_setup_completed()
                logger.info("Setup marked as completed")
                return {'message': 'Setup completed successfully'}, 200
            
            return {'message': 'Invalid request'}, 400
            
        except Exception as e:
            logger.error(f"Error updating setup status: {e}")
            api.abort(500, str(e))

@api.route('/acestream_status')
class AcestreamStatus(Resource):
    @api.doc('get_acestream_status')
    @api.marshal_with(acestream_status_model)
    def get(self):
        """Get Acestream Engine status."""
        config = Config()
        
        # Create service instance and get status
        service = AcestreamStatusService(engine_url=config.ace_engine_url)
        status = service.check_status()
        
        return status

@api.route('/addpid')
class AddPid(Resource):
    @api.doc('get_addpid')
    def get(self):
        """Get whether to add PID parameter to URLs."""
        try:
            config = Config()
            return {"addpid": config.addpid}
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('update_addpid')
    @api.expect(addpid_model)
    def put(self):
        """Update whether to add PID parameter to URLs."""
        data = request.json
        addpid = data.get('addpid')
        
        if addpid is None:
            api.abort(400, "addpid is required")
        
        try:
            config = Config()
            config.addpid = addpid
            return {"message": "PID parameter setting updated successfully"}
        except Exception as e:
            api.abort(500, str(e))

@api.route('/acexy_check_interval')
class AcexyCheckInterval(Resource):
    @api.doc('get_acexy_check_interval')
    def get(self):
        """Get Acexy status check interval."""
        try:
            # Get from localStorage via cookie or use default
            default_interval = 60  # Default to 60 seconds
            return {"interval": default_interval}
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('update_acexy_check_interval')
    @api.expect(status_check_interval_model)
    def put(self):
        """Update Acexy status check interval."""
        data = request.json
        interval = data.get('interval')
        
        if interval is None or interval < 5:  # Minimum 5 seconds
            api.abort(400, "interval must be at least 5 seconds")
        
        try:
            # Store in config (will be handled client-side with localStorage)
            return {"message": "Acexy check interval updated successfully"}
        except Exception as e:
            api.abort(500, str(e))

@api.route('/acestream_check_interval')
class AcestreamCheckInterval(Resource):
    @api.doc('get_acestream_check_interval')
    def get(self):
        """Get Acestream Engine status check interval."""
        try:
            # Get from localStorage via cookie or use default
            default_interval = 120  # Default to 120 seconds
            return {"interval": default_interval}
        except Exception as e:
            api.abort(500, str(e))
    
    @api.doc('update_acestream_check_interval')
    @api.expect(status_check_interval_model)
    def put(self):
        """Update Acestream Engine status check interval."""
        data = request.json
        interval = data.get('interval')
        
        if interval is None or interval < 5:  # Minimum 5 seconds
            api.abort(400, "interval must be at least 5 seconds")
        
        try:
            # Store in config (will be handled client-side with localStorage)
            return {"message": "Acestream Engine check interval updated successfully"}
        except Exception as e:
            api.abort(500, str(e))

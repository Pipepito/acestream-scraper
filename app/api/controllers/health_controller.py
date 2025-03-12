from flask_restx import Namespace, Resource, fields
import requests
from requests.exceptions import RequestException
from app.utils.config import Config
import os
import logging

logger = logging.getLogger(__name__)

api = Namespace('health', description='Health check endpoints')

health_model = api.model('HealthStatus', {
    'status': fields.String(required=True, description='System health status'),
    'app': fields.Boolean(required=True, description='Application status'),
    'database': fields.Boolean(required=True, description='Database status'),
    'acexy': fields.Boolean(description='Acexy service status (if enabled)'),
    'acestream': fields.Boolean(description='Acestream Engine status (if enabled)'),
    'task_manager': fields.Boolean(description='Task manager status'),
    'details': fields.Raw(description='Additional status details')
})

@api.route('/')
class HealthCheck(Resource):
    @api.doc('health_check')
    @api.marshal_with(health_model)
    def get(self):
        """Get system health status"""
        health_data = {
            'status': 'healthy',
            'app': True,
            'database': True,
            'acexy': None,
            'acestream': None,
            'task_manager': False,
            'details': {}
        }
        
        try:
            # Check database
            try:
                from app.extensions import db
                db.session.execute('SELECT 1')
            except Exception as e:
                logger.error(f"Database check failed: {str(e)}")
                health_data['database'] = False
                health_data['status'] = 'degraded'
                health_data['details']['database_error'] = str(e)
            
            # Check Acexy and Acestream
            acexy_enabled = os.environ.get("ENABLE_ACEXY", "false").lower() == "true"
            acestream_enabled = os.environ.get("ENABLE_ACESTREAM_ENGINE", "false").lower() == "true"
            
            if acexy_enabled:
                try:
                    # Use requests Session to handle SSL/cert issues
                    session = requests.Session()
                    session.verify = False  # Disable SSL verification for local calls
                    
                    response = session.get('http://localhost:8080/ace/status', 
                                        timeout=2,
                                        headers={'Accept': 'application/json'})
                    
                    health_data['acexy'] = response.status_code == 200
                    if not health_data['acexy']:
                        health_data['status'] = 'degraded'
                        health_data['details']['acexy_error'] = f'Service returned {response.status_code}'
                except RequestException as e:
                    logger.error(f"Acexy check failed: {str(e)}")
                    health_data['acexy'] = False
                    health_data['status'] = 'degraded'
                    health_data['details']['acexy_error'] = str(e)
                
                # Check Acestream Engine
                if acestream_enabled:
                    try:
                        config = Config()
                        response = session.get(
                            f"{config.ace_engine_url}/webui/api/service",
                            timeout=2,
                            headers={'Accept': 'application/json'}
                        )
                        health_data['acestream'] = response.status_code == 200
                        if not health_data['acestream']:
                            health_data['status'] = 'degraded'
                            health_data['details']['acestream_error'] = f'Service returned {response.status_code}'
                    except RequestException as e:
                        logger.error(f"Acestream check failed: {str(e)}")
                        health_data['acestream'] = False
                        health_data['status'] = 'degraded'
                        health_data['details']['acestream_error'] = str(e)
            
            # Check Task Manager
            try:
                from app.views.main import task_manager
                if task_manager:
                    health_data['task_manager'] = task_manager.running
                    if not health_data['task_manager']:
                        health_data['status'] = 'degraded'
                        health_data['details']['task_manager_error'] = 'Not running'
                else:
                    health_data['details']['task_manager_error'] = 'Task manager not initialized'
            except Exception as e:
                logger.error(f"Task manager check failed: {str(e)}")
                health_data['task_manager'] = False
                health_data['status'] = 'degraded'
                health_data['details']['task_manager_error'] = str(e)

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            health_data['status'] = 'error'
            health_data['app'] = False
            health_data['details']['error'] = str(e)
        
        return health_data
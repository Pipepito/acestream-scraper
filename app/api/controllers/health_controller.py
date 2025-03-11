from flask_restx import Namespace, Resource, fields
import requests
from app.utils.config import Config
import os

api = Namespace('health', description='Health check endpoints')

health_model = api.model('HealthStatus', {
    'status': fields.String(required=True, description='System health status'),
    'app': fields.Boolean(required=True, description='Application status'),
    'database': fields.Boolean(required=True, description='Database status'),
    'acexy': fields.Boolean(description='Acexy service status (if enabled)'),
    'task_manager': fields.Boolean(description='Task manager status')
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
            'task_manager': False
        }
        
        try:
            from app.extensions import db
            db.session.execute('SELECT 1')
        except Exception as e:
            health_data['database'] = False
            health_data['status'] = 'degraded'
        
        acexy_enabled = os.environ.get("ENABLE_ACEXY", "false").lower() == "true"
        if acexy_enabled:
            try:
                response = requests.get('http://localhost:8080/ace/status', timeout=2)
                health_data['acexy'] = response.status_code == 200
                if not health_data['acexy']:
                    health_data['status'] = 'degraded'
            except Exception:
                health_data['acexy'] = False
                health_data['status'] = 'degraded'
        
        from app.views.main import task_manager
        if task_manager:
            health_data['task_manager'] = task_manager.running
            if not health_data['task_manager']:
                health_data['status'] = 'degraded'
        
        return health_data
from flask import jsonify
import logging
from flask_restx import Resource

logger = logging.getLogger(__name__)

def register_routes(api):
    """Register configuration routes."""
    
    @api.route("/migrate_config", endpoint="migrate_config")
    class MigrateConfig(Resource):
        @api.doc('migrate_config')
        def post(self):
            """Migrate settings from config.json to the database."""
            try:
                from app.utils.config import Config
                config = Config()
                success = config.migrate_to_database()
                
                if success:
                    return {"status": "success", "message": "Configuration successfully migrated from file to database"}
                else:
                    return {"status": "error", "message": "Failed to migrate configuration or no file exists"}
            except Exception as e:
                import traceback
                logger.error(f"Error migrating config: {str(e)}\n{traceback.format_exc()}")
                return {"status": "error", "message": f"Error: {str(e)}"}, 500

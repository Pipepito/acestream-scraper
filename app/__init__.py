import os
import asyncio
import threading
from flask import Flask, redirect, url_for, request
from app.extensions import db, migrate
from app.utils.config import Config
from app.repositories import SettingsRepository
from app.tasks.manager import TaskManager

# Make task_manager accessible globally
task_manager = None

def create_app(test_config=None):
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.debug = True  # Add this line to enable detailed error messages
    
    # Load configuration
    config = Config()
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize task manager
    global task_manager
    task_manager = TaskManager()
    task_manager.init_app(app)
    
    # Start task manager in a background thread
    def run_task_manager():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(task_manager.start())
        
    task_thread = threading.Thread(target=run_task_manager, daemon=True)
    task_thread.start()
    
    # Import views here to avoid circular imports
    from app.views import main
    
    # Register blueprints
    app.register_blueprint(main.bp)
    
    # Make task manager available in main views
    main.task_manager = task_manager
    
    # Register API blueprints
    try:
        from app.api import bp as api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
    except ImportError as e:
        app.logger.warning(f"Could not register API: {str(e)}")
    
    # Set up settings repository after database is initialized
    with app.app_context():
        db.create_all()
        settings_repo = SettingsRepository()
        config.set_settings_repository(settings_repo)
        
        # Check if setup is needed
        @app.before_request
        def check_setup():
            # Skip for static files and setup page itself
            if request.path.startswith('/static') or request.path == '/setup':
                return None
                
            if not config.is_initialized() and request.path != '/setup':
                return redirect(url_for('main.setup'))
    
    return app
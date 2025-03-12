import os
import asyncio
import threading
import logging
from pathlib import Path
from flask import Flask, redirect, url_for, request
from werkzeug.middleware.proxy_fix import ProxyFix
from app.extensions import db, migrate
from app.utils.config import Config
from app.repositories import SettingsRepository
from app.tasks.manager import TaskManager

# Make task_manager accessible globally
task_manager = None

def create_app(test_config=None):
    """Create and configure the Flask app."""
    global task_manager  # Move global declaration to the beginning of the function
    if not task_manager:
        task_manager = TaskManager()
        
    app = Flask(__name__)
    
    # Add middleware to handle SSL/proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Force HTTP scheme internally
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    # Disable SSL requirement for internal API calls
    app.config['SWAGGER_SUPPORTED_SUBMIT_METHODS'] = ['get', 'post', 'put', 'delete']
    app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
    
    # Configure logging
    logging_level = logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Set default configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['DEBUG'] = os.environ.get('FLASK_ENV') == 'development'
    
    # Load configuration from Config singleton
    try:
        config = Config()
        
        # Ensure config directory exists before initializing database
        if config.database_path:
            config_dir = config.database_path.parent
            config_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensuring config directory exists: {config_dir}")
        
        app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    except Exception as e:
        logger.error(f"Error configuring application: {e}")
        # Fallback to in-memory database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register API blueprint (needed for both regular and test modes)
    try:
        from app.api import bp as api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api')
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not register API blueprint: {e}")
    
    # Always register main blueprint for both test and non-test environments
    # to ensure routes like /playlist.m3u are available in tests
    is_testing = test_config == 'testing' or os.environ.get('TESTING') == '1'
    try:
        # Fix: Import the blueprint object 'bp' from views.main, not the module 'main'
        from app.views.main import bp as main_blueprint
        app.register_blueprint(main_blueprint)
        
        # Make test mode available to routes
        app.config['TESTING'] = is_testing
        
        # For backward compatibility - make task_manager available to views
        if hasattr(main_blueprint, 'task_manager') and task_manager:
            main_blueprint.task_manager = task_manager
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not register main blueprint: {e}")
    
    # Initialize settings repository after database initialization
    with app.app_context():
        try:
            logger.info("Creating database tables (if they don't exist)...")
            db.create_all()
            logger.info("Database tables setup completed")
            
            # Set the settings repository in the Config singleton
            settings_repo = SettingsRepository()
            config.set_settings_repository(settings_repo)
            
            # Initialize async task manager only in non-testing mode 
            if not is_testing:
                task_manager.init_app(app)
                
                # Start task manager in a background thread
                def run_task_manager():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(task_manager.start())
                    
                thread = threading.Thread(target=run_task_manager, daemon=True)
                thread.start()
                
        except Exception as e:
            logger.error(f"Error during app initialization: {e}")
    
    # Add a route to redirect root URL to the dashboard
    @app.route('/')
    def index():
        # Use _external=False to avoid potential scheme issues in tests
        return redirect(url_for('main.dashboard'))
    
    return app
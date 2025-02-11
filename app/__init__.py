import asyncio
import os
from flask import Flask
from .extensions import db
from .utils.config import Config
from .tasks.manager import TaskManager

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    
    # Load configuration
    config = Config()
    
    # Ensure config directory exists
    os.makedirs(config.config_path, exist_ok=True)
    
    # Configure Flask app
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Initialize task manager
    task_manager = TaskManager()
    
    @app.before_first_request
    def start_task_manager():
        loop = asyncio.get_event_loop()
        loop.create_task(task_manager.start())
    
    @app.teardown_appcontext
    async def stop_task_manager(exception=None):
        await task_manager.stop()
    
    return app
import os
import asyncio
import threading
from flask import Flask
from .extensions import db
from .utils.config import Config
from .tasks.manager import TaskManager
from .views.main import bp, task_manager  # Import the task_manager reference

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
    
    # Register blueprint after task manager is initialized
    app.register_blueprint(bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app
import asyncio
from flask import Flask
from .extensions import db
from .views.main import bp
from .tasks.manager import TaskManager
from .utils.config import Config

# Global task manager instance
task_manager = None

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    config = Config()
    
    # Configure Flask app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acestream.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

def run_task_manager():
    """Run task manager in the main thread's event loop"""
    global task_manager
    if task_manager is None:
        task_manager = TaskManager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(task_manager.start())
        loop.run_forever()

def main():
    app = create_app()
    
    # Start task manager in a separate thread
    import threading
    task_thread = threading.Thread(target=run_task_manager, daemon=True)
    task_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
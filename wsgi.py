import os
import sys
import logging
import subprocess
from gunicorn.app.base import BaseApplication
from app import create_app
from app.tasks.manager import TaskManager
import threading
import asyncio
from asgiref.wsgi import WsgiToAsgi

# Setup basic logging for migrations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GunicornApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application

def start_task_manager(app):
    """Start task manager in a separate thread"""
    task_manager = TaskManager()
    task_manager.init_app(app)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(task_manager.start())
    loop.run_forever()

# Run database migrations before creating the app
try:
    logger.info("Running database migrations from wsgi.py...")
    subprocess.run([sys.executable, "manage.py", "upgrade"], check=True)
    logger.info("Database migrations completed successfully")
except subprocess.CalledProcessError as e:
    logger.error(f"Failed to run database migrations: {e}")
    # Continue anyway as the app might still work with existing schema
except Exception as e:
    logger.error(f"Unexpected error during database migrations: {e}")
    # Continue anyway as the app might still work with existing schema

flask_app = create_app()
asgi_app = WsgiToAsgi(flask_app)  # Convert WSGI app to ASGI

# Use this for running with Python directly
app = asgi_app

if __name__ == '__main__':
    options = {
        'bind': '0.0.0.0:8000',
        'workers': 3,
        'timeout': 300,
        'keepalive': 5,
        'worker_class': 'uvicorn.workers.UvicornWorker'
    }
    GunicornApplication(asgi_app, options).run()
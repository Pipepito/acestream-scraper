import os
from gunicorn.app.base import BaseApplication
from app import create_app
from app.tasks.manager import TaskManager
import threading
import asyncio

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

if __name__ == '__main__':
    flask_app = create_app()
    
    # Start task manager in a daemon thread
    task_thread = threading.Thread(target=start_task_manager, args=(flask_app,))
    task_thread.daemon = True
    task_thread.start()
    
    # Gunicorn configuration
    options = {
        'bind': f"0.0.0.0:{os.getenv('FLASK_PORT', '8000')}",
        'workers': 3,
        'worker_class': 'sync',
        'threads': 2,
        'timeout': 120,
        'keepalive': 5,
        'max_requests': 10000,
        'max_requests_jitter': 1000,
        'errorlog': '-',
        'accesslog': '-',
        'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    }
    
    GunicornApplication(flask_app, options).run()
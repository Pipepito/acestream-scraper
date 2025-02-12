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

app = create_app()

if __name__ == '__main__':
    app.run()
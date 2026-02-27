from typing import List, Optional
from datetime import datetime
from app.models.background_task_status import BackgroundTaskStatus

# This is a placeholder. In production, integrate with your scheduler/task manager.
class BackgroundTaskStatusService:
    def __init__(self):
        # In-memory store for demonstration; replace with persistent or scheduler-backed store
        self._tasks = {
            "epg_refresh": BackgroundTaskStatus(
                task_name="epg_refresh",
                last_run=None,
                next_run=None,
                status="idle",
                last_error=None,
                last_result=None
            ),
            "playlist_generation": BackgroundTaskStatus(
                task_name="playlist_generation",
                last_run=None,
                next_run=None,
                status="idle",
                last_error=None,
                last_result=None
            ),
            # Add more tasks as needed
        }

    def get_all_statuses(self) -> List[BackgroundTaskStatus]:
        return list(self._tasks.values())

    def update_status(self, task_name: str, **kwargs):
        if task_name in self._tasks:
            for k, v in kwargs.items():
                setattr(self._tasks[task_name], k, v)
        else:
            self._tasks[task_name] = BackgroundTaskStatus(task_name=task_name, **kwargs)

    def get_status(self, task_name: str) -> Optional[BackgroundTaskStatus]:
        return self._tasks.get(task_name)

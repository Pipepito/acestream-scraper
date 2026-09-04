from typing import Dict, List, Optional
from app.models.background_task_status import BackgroundTaskStatus
from app.services.task_service import task_service

class BackgroundTaskStatusService:
    def __init__(self):
        self._task_service = task_service

    def _base_payload(self, task_name: str) -> Dict[str, object]:
        state = self._task_service.get_task_state(task_name) or {}
        return {
            "task_name": task_name,
            "last_run": state.get("last_run"),
            "next_run": state.get("next_run"),
            "status": state.get("status", "idle"),
            "last_error": state.get("last_error"),
            "last_result": state.get("last_result"),
            "progress": state.get("progress"),
        }

    def get_all_statuses(self) -> List[BackgroundTaskStatus]:
        statuses: List[BackgroundTaskStatus] = []
        jobs = self._task_service.get_jobs()
        seen = set()

        for job in jobs:
            task_name = job.id
            payload = self._base_payload(task_name)
            payload["next_run"] = job.next_run_time
            statuses.append(BackgroundTaskStatus(**payload))
            seen.add(task_name)

        for task_name, state in self._task_service.get_task_states().items():
            if task_name in seen:
                continue
            statuses.append(BackgroundTaskStatus(**self._base_payload(task_name)))

        return sorted(statuses, key=lambda status: status.task_name)

    def update_status(self, task_name: str, **kwargs):
        raise NotImplementedError("Task status is scheduler-driven and cannot be manually updated.")

    def get_status(self, task_name: str) -> Optional[BackgroundTaskStatus]:
        for status in self.get_all_statuses():
            if status.task_name == task_name:
                return status
        return None

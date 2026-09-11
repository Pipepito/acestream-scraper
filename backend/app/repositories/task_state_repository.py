"""Bounded latest-run storage: one row per scheduled task, no runtime objects."""
from app.config.database import SessionLocal
from app.models.models import ScheduledTaskState


class TaskStateRepository:
    def load(self):
        with SessionLocal() as db:
            return {row.task_name: {
                'task_name': row.task_name, 'last_run': row.last_run,
                'status': row.status, 'last_error': row.last_error,
                'last_result': row.last_result, 'next_run': None, 'progress': None,
            } for row in db.query(ScheduledTaskState).all()}

    def save(self, state):
        with SessionLocal() as db:
            row = db.get(ScheduledTaskState, state['task_name'])
            if row is None:
                row = ScheduledTaskState(task_name=state['task_name'])
                db.add(row)
            for key in ('last_run', 'status', 'last_error', 'last_result'):
                setattr(row, key, state.get(key))
            db.commit()

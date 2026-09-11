"""Persist schedule anchors together in the existing settings table."""
from app.schemas.config import ScheduleAnchors
from app.repositories.settings_repository import SettingsRepository


class ScheduleConfigService:
    def __init__(self, db):
        self.repository = SettingsRepository(db)

    def get(self) -> ScheduleAnchors:
        raw = self.repository.get_setting("schedule_anchors")
        return ScheduleAnchors.model_validate_json(raw) if raw else ScheduleAnchors()

    def save(self, schedule: ScheduleAnchors) -> bool:
        return self.repository.set_setting("schedule_anchors", schedule.model_dump_json())


def load_schedule_anchors():
    from app.config.database import SessionLocal
    with SessionLocal() as db:
        return ScheduleConfigService(db).get()

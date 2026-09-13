from sqlalchemy.orm import Session
from app.models.models import DashboardConfig
from typing import Optional

class DashboardConfigService:
    def __init__(self, db: Session):
        self.db = db

    def get_config(self) -> DashboardConfig:
        config = self.db.query(DashboardConfig).first()
        if not config:
            config = DashboardConfig()
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        return config

    def update_config(self, retention_days: Optional[int] = None, auto_refresh_interval: Optional[int] = None) -> DashboardConfig:
        config = self.get_config()
        if retention_days is not None:
            config.retention_days = max(0, min(30, retention_days))
        if auto_refresh_interval is not None:
            config.auto_refresh_interval = max(10, min(600, auto_refresh_interval))
        self.db.commit()
        self.db.refresh(config)
        return config

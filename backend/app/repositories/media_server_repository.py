"""DB access for media servers (spec 7.3)."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import MediaServer


class MediaServerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[MediaServer]:
        return self.db.query(MediaServer).order_by(MediaServer.name).all()

    def get(self, server_id: int) -> Optional[MediaServer]:
        return self.db.query(MediaServer).filter(MediaServer.id == server_id).first()

    def get_by_name(self, name: str) -> Optional[MediaServer]:
        return self.db.query(MediaServer).filter(MediaServer.name == name).first()

    def create(self, *, kind: str, name: str, base_url: str, api_key: Optional[str], tuner_mode: str = "hdhomerun",
               enabled: bool = True, auto_refresh: bool = True) -> MediaServer:
        entry = MediaServer(kind=kind, name=name, base_url=base_url, api_key=api_key, tuner_mode=tuner_mode, enabled=enabled, auto_refresh=auto_refresh)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def save(self, entry: MediaServer) -> MediaServer:
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: MediaServer) -> None:
        self.db.delete(entry)
        self.db.commit()

"""DB access for remote players (spec 6.1)."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import RemotePlayer

_KEEP = object()


class RemotePlayerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[RemotePlayer]:
        return self.db.query(RemotePlayer).order_by(RemotePlayer.name).all()

    def get(self, player_id: int) -> Optional[RemotePlayer]:
        return self.db.query(RemotePlayer).filter(RemotePlayer.id == player_id).first()

    def get_by_name(self, name: str) -> Optional[RemotePlayer]:
        return self.db.query(RemotePlayer).filter(RemotePlayer.name == name).first()

    def create(
        self,
        *,
        name: str,
        kind: str,
        host: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
        base_url_id: Optional[int],
    ) -> RemotePlayer:
        entry = RemotePlayer(
            name=name,
            kind=kind,
            host=host,
            port=port,
            username=username,
            password=password,
            base_url_id=base_url_id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(
        self,
        entry: RemotePlayer,
        *,
        name=_KEEP,
        kind=_KEEP,
        host=_KEEP,
        port=_KEEP,
        username=_KEEP,
        password=_KEEP,
        base_url_id=_KEEP,
    ) -> RemotePlayer:
        """Patch semantics: an omitted or None value keeps the stored one.

        A password of "" clears the stored secret; None keeps it (the UI
        leaves the field empty when the password is unchanged). Detaching a
        player from its stream link format goes through clear_base_url().
        """
        for field, value in (
            ("name", name),
            ("kind", kind),
            ("host", host),
            ("port", port),
            ("username", username),
            ("base_url_id", base_url_id),
        ):
            if value is not _KEEP and value is not None:
                setattr(entry, field, value)
        if password is not _KEEP and password is not None:
            entry.password = password
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def clear_base_url(self, entry: RemotePlayer) -> RemotePlayer:
        """Send this player the backend relay URL again (base_url_id = NULL)."""
        entry.base_url_id = None
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: RemotePlayer) -> None:
        self.db.delete(entry)
        self.db.commit()

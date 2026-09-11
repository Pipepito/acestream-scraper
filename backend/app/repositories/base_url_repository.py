"""
Repository for named stream base URLs (#62).
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import BaseUrl


class BaseUrlRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[BaseUrl]:
        return self.db.query(BaseUrl).order_by(BaseUrl.id).all()

    def get(self, base_url_id: int) -> Optional[BaseUrl]:
        return self.db.query(BaseUrl).filter(BaseUrl.id == base_url_id).first()

    def get_by_name(self, name: str) -> Optional[BaseUrl]:
        return self.db.query(BaseUrl).filter(BaseUrl.name == name).first()

    def get_default(self) -> Optional[BaseUrl]:
        default = self.db.query(BaseUrl).filter(BaseUrl.is_default.is_(True)).first()
        if default:
            return default
        # With exactly one entry there is no ambiguity (#62: "if there's
        # only one assume it's the default").
        entries = self.db.query(BaseUrl).limit(2).all()
        return entries[0] if len(entries) == 1 else None

    def create(self, name: str, pattern: str, is_default: bool = False) -> BaseUrl:
        if is_default:
            self._clear_default()
        entry = BaseUrl(name=name, pattern=pattern, is_default=is_default)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry: BaseUrl, name: Optional[str] = None,
               pattern: Optional[str] = None, is_default: Optional[bool] = None) -> BaseUrl:
        if name is not None:
            entry.name = name
        if pattern is not None:
            entry.pattern = pattern
        if is_default is not None:
            if is_default:
                self._clear_default()
            entry.is_default = is_default
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: BaseUrl) -> None:
        self.db.delete(entry)
        self.db.commit()

    def _clear_default(self) -> None:
        self.db.query(BaseUrl).filter(BaseUrl.is_default.is_(True)).update(
            {BaseUrl.is_default: False}
        )

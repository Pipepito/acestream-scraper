from sqlalchemy.orm import Session

from app.repositories.url_repository import URLRepository

class URLService:
    def __init__(self, db: Session):
        self.repository = URLRepository(db)

    def refresh_url(self, url_id: int) -> bool:
        return self.repository.refresh_url(url_id)

    def refresh_all_urls(self) -> int:
        return self.repository.refresh_all_urls()

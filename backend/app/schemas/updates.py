"""Public release discovery; no installation or updater controls."""
from typing import Literal
from pydantic import BaseModel


class UpdateStatus(BaseModel):
    current_version: str
    latest_version: str | None = None
    update_available: bool = False
    release_url: str | None = None
    deployment: Literal['docker', 'native']
    status: Literal['checked', 'unavailable']

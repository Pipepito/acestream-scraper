"""Container-visible storage; host bind paths and Docker volume names are unknown."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class StorageDirectory(BaseModel):
    path: str
    mounted: bool | None = None
    mount_point: str | None = None
    read_only: bool | None = None
    directory_bytes: int | None = None
    size_complete: bool = False
    filesystem_total_bytes: int | None = None
    filesystem_free_bytes: int | None = None
    message: str = ''


class ConfigurationWarning(BaseModel):
    legacy: str
    replacement: str
    selected: str


class StorageReport(BaseModel):
    checked_at: datetime
    directories: list[StorageDirectory]
    mount_detection: Literal['available', 'unavailable']
    configuration_warnings: list[ConfigurationWarning] = []
    message: str = ''

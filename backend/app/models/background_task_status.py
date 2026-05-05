from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class BackgroundTaskStatus(BaseModel):
    task_name: str
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    status: str  # e.g. 'idle', 'running', 'error'
    last_error: Optional[str]
    last_result: Optional[Dict[str, Any]]

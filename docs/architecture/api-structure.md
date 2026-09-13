# API & DTO Structure (FastAPI + Pydantic)

## Principles

- **Every endpoint uses a well-documented Pydantic DTO for input/output.**
- **Every DTO has type hints, docstrings, and descriptive fields.**
- **The OpenAPI schema is always up-to-date and used for frontend API codegen.**

## Example DTOs

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ChannelDTO(BaseModel):
    """Acestream channel with EPG and metadata."""
    id: str = Field(..., description="Acestream channel ID (hash)")
    name: str = Field(..., description="Channel display name")
    tvg_id: Optional[str] = Field(None, description="EPG TVG ID")
    tvg_name: Optional[str] = Field(None, description="EPG TVG Name")
    logo: Optional[str] = Field(None, description="Channel logo URL")
    group: Optional[str] = Field(None, description="Channel group/category")
    is_online: bool = Field(..., description="Online status")
```

```python
class PlaylistRequestDTO(BaseModel):
    """Request parameters for generating a playlist."""
    search: Optional[str] = Field(None, description="Search filter for channels")
    refresh: Optional[bool] = Field(False, description="Force refresh")
```

## Example API Endpoints

```python
from fastapi import APIRouter, Depends
from typing import List
from app.dtos.channel import ChannelDTO
from app.services.channel_service import ChannelService

router = APIRouter(prefix="/channels", tags=["channels"])

@router.get("/", response_model=List[ChannelDTO])
async def list_channels(service: ChannelService = Depends()):
    """List all channels."""
    return await service.get_all_channels()

@router.get("/{channel_id}", response_model=ChannelDTO)
async def get_channel(channel_id: str, service: ChannelService = Depends()):
    """Get channel by ID."""
    return await service.get_channel(channel_id)
```

## OpenAPI/Swagger

- FastAPI automatically exposes `/openapi.json` and `/docs`.
- Use this for frontend API codegen.

## Versioning

- All endpoints are under `/api/v1/` (e.g., `/api/v1/channels/`).

---

**Frontend should only use the generated API client for communication.**
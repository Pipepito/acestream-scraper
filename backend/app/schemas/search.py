from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional

class SearchResultItem(BaseModel):
    id: str = Field(..., description="Acestream channel ID (infohash)")
    name: str = Field(..., min_length=1, max_length=512, description="Channel name")
    bitrate: Optional[int] = Field(None, description="Channel bitrate")
    categories: List[str] = Field(default_factory=list, description="Categories of the channel")
    status: Optional[int] = Field(None, description="Catalogue status: 2 available, 1 uncertain; not a live probe")
    availability: Optional[float] = Field(None, description="Catalogue availability score")
    availability_updated_at: Optional[int] = Field(None, description="Unix timestamp of the catalogue availability update")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("name", mode="before")
    @classmethod
    def _name_as_text(cls, v):
        """The engine catalogue returns purely numeric names as JSON numbers.

        A single such entry made FastAPI reject the whole response with a 500,
        taking the entire search endpoint down for every query whose page
        happened to contain it.
        """
        if isinstance(v, bool) or v is None:
            return v
        if isinstance(v, (int, float)):
            return str(v)
        return v

class SearchPagination(BaseModel):
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_results: int = Field(..., description="Total number of results")
    total_pages: int = Field(..., description="Total number of pages")


class ResolvedSearchResult(BaseModel):
    content_id: str = Field(..., pattern=r"^[0-9a-f]{40}$", description="Resolved transport-file content ID for saving or playback")

class SearchResponse(BaseModel):
    success: bool = Field(..., description="Success status of the request")
    message: str = Field(..., description="Message describing the result")
    results: List[SearchResultItem] = Field(default_factory=list, description="Search results")
    pagination: SearchPagination = Field(..., description="Pagination information")

class AddChannelRequest(BaseModel):
    id: str = Field(pattern=r"^[0-9a-fA-F]{40}$", description="Catalogue infohash; resolved by the server before import")
    name: str = Field(..., min_length=1, max_length=512, description="Channel name")
    url: str = Field(..., description="Channel URL")
    category: Optional[str] = Field(None, description="Channel category")
    description: Optional[str] = Field(None, description="Channel description")
    logo: Optional[str] = Field(None, description="Channel logo URL")
    tv_channel_id: Optional[int] = Field(None, description="TV channel ID for association")

class AddMultipleRequest(BaseModel):
    channels: List[AddChannelRequest] = Field(..., min_length=1, max_length=100, description="Catalogue results to resolve and import")


class SearchImportItem(BaseModel):
    infohash: str = Field(pattern=r'^[a-fA-F0-9]{40}$')
    name: str = Field(min_length=1, max_length=512)
    category: str = Field(default='', max_length=100)


class SearchImportRequest(BaseModel):
    items: list[SearchImportItem] = Field(min_length=1, max_length=100)


from typing import Literal


class SearchImportOutcome(BaseModel):
    infohash: str
    content_id: str | None = None
    outcome: Literal['added', 'existing', 'excluded', 'unresolved', 'duplicate', 'deferred']
    rule_ids: list[int] = Field(default_factory=list)


class SearchImportResponse(BaseModel):
    items: list[SearchImportOutcome]
    policy_revision: int
    added: int = 0
    existing: int = 0
    excluded: int = 0
    unresolved: int = 0
    deferred: int = 0

from pydantic import BaseModel, Field
from typing import List, Optional

class SearchResultItem(BaseModel):
    id: str = Field(..., description="Acestream channel ID (infohash)")
    name: str = Field(..., description="Channel name")
    bitrate: Optional[int] = Field(None, description="Channel bitrate")
    categories: List[str] = Field(default_factory=list, description="Categories of the channel")

    class Config:
        from_attributes = True

class SearchPagination(BaseModel):
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_results: int = Field(..., description="Total number of results")
    total_pages: int = Field(..., description="Total number of pages")

class SearchResponse(BaseModel):
    success: bool = Field(..., description="Success status of the request")
    message: str = Field(..., description="Message describing the result")
    results: List[SearchResultItem] = Field(default_factory=list, description="Search results")
    pagination: SearchPagination = Field(..., description="Pagination information")

class AddChannelRequest(BaseModel):
    id: Optional[str] = Field(None, description="Acestream channel ID (optional, will be generated if not provided)")
    name: str = Field(..., description="Channel name")
    url: str = Field(..., description="Channel URL")
    category: Optional[str] = Field(None, description="Channel category")
    description: Optional[str] = Field(None, description="Channel description")
    logo: Optional[str] = Field(None, description="Channel logo URL")
    tv_channel_id: Optional[int] = Field(None, description="TV channel ID for association")

class AddMultipleRequest(BaseModel):
    channels: List[AddChannelRequest] = Field(..., description="List of channels to add")

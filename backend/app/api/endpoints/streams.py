from fastapi import APIRouter
from app.services.streams_service import StreamsService

router = APIRouter()

streams_service = StreamsService()

@router.get("/streams/active", tags=["streams"])
def get_active_streams():
    return streams_service.get_active_streams_count()

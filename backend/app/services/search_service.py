from typing import Dict, Any, List, Optional, Tuple
import logging
import requests
import json
from fastapi import HTTPException

from app.config.settings import get_settings
from app.repositories.channel_repository import ChannelRepository
from app.repositories.url_repository import URLRepository
from app.services.channel_service import ChannelService
from app.schemas.search import AddChannelRequest, AddMultipleRequest
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class SearchService:
    """Service for searching Acestream channels via the engine API."""

    def __init__(self, config_service=None, db: Session = None):
        """Initialize search service with engine URL from config service."""
        self.config_service = config_service
        self._engine_url = None
        self.db = db
        if db:
            self.channel_repo = ChannelRepository(db)
            self.url_repo = URLRepository(db)
            self.channel_service = ChannelService(db)
        else:
            self.channel_repo = None
            self.url_repo = None
            self.channel_service = None

    def _get_engine_url(self) -> str:
        """Get engine URL from config service or fallback to default."""
        if self._engine_url:
            return self._engine_url

        if self.config_service:
            engine_url = self.config_service.get_ace_engine_url()
        else:
            # Fallback to default
            engine_url = "http://127.0.0.1:6878"

        # If URL doesn't start with a protocol, assume http://
        if not engine_url.startswith('http'):
            engine_url = f"http://{engine_url}"

        # Ensure the URL doesn't end with a slash
        engine_url = engine_url.rstrip('/')

        self._engine_url = engine_url
        logger.debug(f"Acestream Search Service initialized with engine URL: {engine_url}")
        return engine_url

    async def search(self, query: str = "", page: int = 1, page_size: int = 10, category: str = "") -> Dict[str, Any]:
        """
        Search for Acestream channels using the engine API.

        Args:
            query: The search query string (optional, defaults to empty string for all channels)
            page: Page number for pagination (1-based)
            page_size: Number of results per page
            category: Filter by category (optional)

        Returns:
            Dict containing search results, pagination info, and status
        """
        try:
            # Construct search URL
            engine_url = self._get_engine_url()
            search_url = f"{engine_url}/search"

            # Convert from 1-based pagination (UI) to 0-based pagination (API)
            api_page = page - 1

            # Prepare query parameters
            params = {
                'query': query,
                'page': api_page,  # Send 0-based page index to the API
                'page_size': page_size
            }

            # Add category parameter if provided
            if category:
                params['category'] = category

            # Make request to Acestream engine

            response = requests.get(search_url, params=params, timeout=10)

            # Enhanced logging - log the actual status code
            logger.info(f"Search API response status code: {response.status_code}")

            # Check if request was successful
            if response.status_code == 200:
                # Log the raw API response for debugging
                raw_response = response.text
                logger.debug(f"Raw API response: {raw_response[:1000]}..." if len(raw_response) > 1000 else raw_response)

                try:
                    search_data = response.json()

                    # Handle the nested structure from Acestream API
                    api_result = search_data.get('result', {})
                    raw_results = api_result.get('results', [])
                    total_results = api_result.get('total', 0)

                    # Transform the results to have a proper ID field
                    processed_results = []

                    for result in raw_results:
                        # Handle the expected structure with 'name' and 'items'
                        if 'items' in result and isinstance(result['items'], list) and len(result['items']) > 0:
                            for item in result['items']:
                                # Create a processed result with the required fields
                                processed_item = {
                                    'name': result.get('name', 'Unnamed Channel'),
                                    'id': item.get('infohash', ''), # Use the infohash as ID
                                    'categories': item.get('categories', []),
                                    'bitrate': item.get('bitrate', 0)
                                }
                                # Add any other useful fields from the item
                                for key, value in item.items():
                                    if key not in processed_item and key != 'infohash':
                                        processed_item[key] = value

                                processed_results.append(processed_item)
                        else:
                            # If the expected structure is not present, try to use the result directly
                            logger.warning(f"Unexpected result structure without 'items': {result}")
                            # Try to extract an ID from the result if possible
                            result_id = result.get('infohash', result.get('id', ''))
                            if result_id:
                                result['id'] = result_id
                                processed_results.append(result)

                    # Log the number of results found
                    logger.debug(f"Extracted {len(processed_results)} processed results from API response")
                    logger.debug(f"Total results reported by API: {total_results}")

                    # Process and structure the response
                    result = {
                        'success': True,
                        'message': 'Search successful',
                        'results': processed_results,
                        'pagination': {
                            'page': page,  # Return the original 1-based page for the UI
                            'page_size': page_size,
                            'total_results': total_results,
                            'total_pages': (total_results + page_size - 1) // page_size if total_results > 0 else 0
                        }
                    }

                    query_description = query if query else "all channels"
                    return result
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse JSON response: {json_err}")
                    logger.error(f"Raw response content (first 500 chars): {response.text[:500]}")
                    raise HTTPException(status_code=500, detail=f"Failed to parse API response: {json_err}")
            else:
                error_msg = f"Acestream search failed with status code {response.status_code}"
                logger.error(error_msg)
                logger.error(f"Response content: {response.text[:500]}..." if len(response.text) > 500 else response.text)
                raise HTTPException(status_code=response.status_code, detail=error_msg)
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Error searching Acestream: {str(e)}"
            logger.error(error_msg)
            logger.exception("Exception details:")
            raise HTTPException(status_code=500, detail=error_msg)

    def extract_acestream_id(self, url: str) -> Optional[str]:
        """
        Extract acestream ID from a URL.

        Args:
            url: Acestream URL

        Returns:
            Extracted ID or None if not found
        """
        if url.startswith('acestream://'):
            return url.split('acestream://')[1]
        return None

    async def add_channel(self, channel: AddChannelRequest):
        """
        Add or update a channel from search results, including TV channel association.
        """
        if not self.db or not self.channel_repo or not self.url_repo:
            raise HTTPException(status_code=500, detail="Database session not initialized")

        # Generate UUID if ID is not provided
        if not channel.id:
            from uuid import uuid4
            channel.id = str(uuid4())

        # Check if channel already exists
        existing_channel = self.channel_repo.get_channel_by_id(channel.id)
        if existing_channel:
            # Update existing channel
            existing_channel.name = channel.name
            existing_channel.source_url = channel.url
            if channel.tv_channel_id:
                self.channel_service.associate_acestream(channel.tv_channel_id, channel.id)
                existing_channel.tv_channel_id = channel.tv_channel_id
            self.db.commit()
            self.db.refresh(existing_channel)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Channel updated successfully",
                    "channel": self.serialize_channel(existing_channel)
                }
            )

        # Create or get the Acestream Search URL entry
        acestream_search_url = self.url_repo.get_or_create_by_type_and_url(
            url_type="search",
            url="Acestream Search",
            trigger_scrape=False
        )

        # Create new channel
        new_channel = self.channel_repo.create_or_update_channel(
            channel_id=channel.id,
            name=channel.name,
            source_url=channel.url
        )
        new_channel.scraped_url_id = acestream_search_url.id
        if channel.tv_channel_id:
            self.channel_service.associate_acestream(channel.tv_channel_id, channel.id)
            new_channel.tv_channel_id = channel.tv_channel_id
        self.db.commit()
        self.db.refresh(new_channel)
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Channel added successfully",
                "channel": self.serialize_channel(new_channel)
            }
        )

    async def add_multiple_channels(self, request: AddMultipleRequest):
        """
        Add or update multiple channels from search results, including TV channel associations.
        """
        if not self.db or not self.channel_repo or not self.url_repo:
            raise HTTPException(status_code=500, detail="Database session not initialized")
        if not request.channels:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "No channels provided",
                    "error": "Empty channel list"
                }
            )
        acestream_search_url = self.url_repo.get_or_create_by_type_and_url(
            url_type="search",
            url="Acestream Search",
            trigger_scrape=False
        )
        added_channels = []
        updated_channels = []
        failed_channels = []
        results = []
        for channel_data in request.channels:
            try:
                if not channel_data.name or not channel_data.url:
                    raise ValueError("Name and URL are required fields")
                if not channel_data.id:
                    from uuid import uuid4
                    channel_data.id = str(uuid4())
                existing_channel = self.channel_repo.get_channel_by_id(channel_data.id)
                if existing_channel:
                    existing_channel.name = channel_data.name
                    existing_channel.source_url = channel_data.url
                    if channel_data.tv_channel_id:
                        self.channel_service.associate_acestream(channel_data.tv_channel_id, channel_data.id)
                        existing_channel.tv_channel_id = channel_data.tv_channel_id
                    updated_channels.append(existing_channel)
                    results.append({
                        "success": True,
                        "message": "Channel updated",
                        "channel": self.serialize_channel(existing_channel)
                    })
                    continue
                new_channel = self.channel_repo.create_or_update_channel(
                    channel_id=channel_data.id,
                    name=channel_data.name,
                    source_url=channel_data.url
                )
                new_channel.scraped_url_id = acestream_search_url.id
                if channel_data.tv_channel_id:
                    self.channel_service.associate_acestream(channel_data.tv_channel_id, channel_data.id)
                    new_channel.tv_channel_id = channel_data.tv_channel_id
                added_channels.append(new_channel)
                results.append({
                    "success": True,
                    "message": "Channel added",
                    "channel": self.serialize_channel(new_channel)
                })
            except Exception as e:
                failed_channels.append({
                    "data": channel_data.dict() if hasattr(channel_data, 'dict') else vars(channel_data),
                    "error": str(e)
                })
                results.append({
                    "success": False,
                    "message": f"Failed to add channel: {str(e)}",
                    "error": str(e)
                })
        self.db.commit()
        total_processed = len(added_channels) + len(updated_channels) + len(failed_channels)
        status_code = 201
        added_channel_objects = [result["channel"] for result in results if result["success"] and result["message"] == "Channel added"]
        response = {
            "success": len(failed_channels) == 0,
            "message": f"{total_processed} channels processed successfully",
            "added_count": len(added_channels),
            "updated_count": len(updated_channels),
            "failed_count": len(failed_channels),
            "results": results,
            "added_channels": added_channel_objects
        }
        return JSONResponse(content=response, status_code=status_code)

    def serialize_channel(self, channel):
        return {
            "id": channel.id,
            "name": channel.name,
            "source_url": channel.source_url,
            "tv_channel_id": getattr(channel, 'tv_channel_id', None),
            "last_checked": channel.last_checked.isoformat() if channel.last_checked else None,
            "last_seen": channel.last_seen.isoformat() if channel.last_seen else None,
            "check_error": channel.check_error,
            "group": channel.group,
            "is_active": channel.is_active,
            "is_online": channel.is_online,
            "epg_update_protected": channel.epg_update_protected
        }

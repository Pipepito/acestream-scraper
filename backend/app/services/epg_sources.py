"""Source management and refresh orchestration. Shared session and service surface supplied by EPGService."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import requests
from app.utils.outbound_http import source_get
from sqlalchemy.orm import Session
from app.models.models import EPGSource, EPGChannel
from app.schemas.epg import EPGSourceCreate, EPGSourceUpdate
from app.utils.url_guard import BlockedURLError, validate_outbound_url
import logging

logger = logging.getLogger(__name__)


class EPGSourceOperations:
    db: Session

    def get_sources(self, skip: int = 0, limit: int = 100) -> List[EPGSource]:
        """Get all EPG sources"""
        return self.db.query(EPGSource).offset(skip).limit(limit).all()

    def get_enabled_sources(self) -> List[EPGSource]:
        """Get all enabled EPG sources"""
        return self.db.query(EPGSource).filter(EPGSource.enabled == True).all()

    def get_source(self, source_id: int) -> Optional[EPGSource]:
        """Get an EPG source by ID"""
        return self.db.query(EPGSource).filter(EPGSource.id == source_id).first()

    def create_source(self, source_data: EPGSourceCreate) -> EPGSource:
        """Create a new EPG source"""
        db_source = EPGSource(
            url=source_data.url,
            name=source_data.name,
            enabled=source_data.enabled
        )
        self.db.add(db_source)
        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    def update_source(self, source_id: int, source_data: EPGSourceUpdate) -> Optional[EPGSource]:
        """Update an EPG source"""
        db_source = self.get_source(source_id)
        if not db_source:
            return None

        update_data = source_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_source, key, value)

        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    def delete_source(self, source_id: int) -> bool:
        """Delete an EPG source"""
        db_source = self.get_source(source_id)
        if not db_source:
            return False

        # Delete dependent EPGChannel objects via the ORM so their
        # cascaded children (programs, string_mappings) are also removed.
        channels = (
            self.db.query(EPGChannel)
            .filter(EPGChannel.epg_source_id == source_id)
            .all()
        )
        for ch in channels:
            self.db.delete(ch)

        self.db.delete(db_source)
        self.db.flush()
        from app.services.epg_link_service import EPGLinkService
        EPGLinkService(self.db).repair()
        self.db.commit()
        return True

    async def refresh_source_async(self, source_id: int) -> Dict[str, Any]:
        """
        Refresh EPG data for a source (async version)

        Args:
            source_id: ID of the EPG source to refresh

        Returns:
            Dict with refresh results
        """
        # Call the synchronous version
        return self.refresh_source(source_id)

    def refresh_source(self, source_id: int) -> Dict[str, Any]:
        """
        Refresh EPG data for a specific source
        Returns a dictionary with refresh results
        """
        start_time = datetime.now()

        try:
            # Get the source
            source = self.get_source(source_id)
            if not source:
                return {
                    "source_id": source_id,
                    "success": False,
                    "error": "Source not found",
                    "channels_found": 0,
                    "programs_found": 0,
                    "duration_seconds": 0
                }

            if not source.enabled:
                return {
                    "source_id": source_id,
                    "success": False,
                    "error": "Source is disabled",
                    "channels_found": 0,
                    "programs_found": 0,
                    "duration_seconds": 0
                }

            logger.info(f"Refreshing EPG source: {source.name} ({source.url})")

            # Fetch EPG data from the source
            result = self._fetch_epg_from_source(source)

            # Update source status
            source.last_updated = datetime.now(timezone.utc)
            if result["success"]:
                source.error_count = 0
                source.last_error = None
            else:
                source.error_count += 1
                source.last_error = result.get("error", "Unknown error")

            self.db.commit()

            if result["success"]:
                from app.services.epg_matching_automation import EPGMatchingAutomation
                EPGMatchingAutomation(self.db).run()

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            result["duration_seconds"] = duration

            logger.info(f"EPG refresh completed for source {source.name}: {result}")
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error refreshing EPG source {source_id}: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "source_id": source_id,
                "success": False,
                "error": str(e),
                "channels_found": 0,
                "programs_found": 0,
                "duration_seconds": duration
            }

    def refresh_all_sources(self) -> List[Dict[str, Any]]:
        """
        Refresh all enabled EPG sources
        Returns a list of refresh results
        """
        sources = self.get_enabled_sources()
        results = []

        for source in sources:
            result = self.refresh_source(source.id)
            results.append(result)

        return results

    def _fetch_epg_from_source(self, source: EPGSource) -> Dict[str, Any]:
        """
        Fetch and parse EPG data from a specific source
        Returns a dictionary with success status and counts
        """
        try:
            logger.info(f"Fetching EPG data from {source.url}")

            # Make HTTP request with timeout. Redirects are followed
            # manually so every hop passes the outbound URL guard.
            current_url = source.url
            validate_outbound_url(current_url)
            response = None
            for _ in range(6):
                response = source_get(current_url, timeout=60, allow_redirects=False)
                if response.is_redirect or response.is_permanent_redirect:
                    location = response.headers.get('Location')
                    if not location:
                        break
                    current_url = urljoin(current_url, location)
                    validate_outbound_url(current_url)
                    continue
                break
            else:
                raise BlockedURLError(f"Too many redirects fetching '{source.url}'")
            response.raise_for_status()

            # Handle gzipped content
            content = response.content
            if source.url.endswith('.gz'):
                import gzip
                content = gzip.decompress(content)

            # Use the improved _process_epg_xml method
            channels_found, programs_found = self._process_epg_xml(source.id, content)

            return {
                "source_id": source.id,
                "success": True,
                "error": None,
                "channels_found": channels_found,
                "programs_found": programs_found
            }

        except requests.RequestException as e:
            return {
                "source_id": source.id,
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "channels_found": 0,
                "programs_found": 0
            }
        except Exception as e:
            return {
                "source_id": source.id,
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "channels_found": 0,
                "programs_found": 0
            }

"""
Integration tests for V2 API endpoints
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import uuid
from unittest.mock import Mock, patch
import sys

# Add v2/backend to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Import V2 app components
from main import app
from app.config.database import Base, get_db
from app.models.models import (
    AcestreamChannel, TVChannel, EPGSource, EPGChannel, EPGProgram,
    ScrapedURL, EPGStringMapping, Setting
)


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a test database for the session."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    # Create test database URL
    database_url = f"sqlite:///{db_path}"

    # Create engine with test database
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine, database_url

    # Clean up - handle Windows file locking issues
    try:
        engine.dispose()  # Close all connections
        os.unlink(db_path)
    except (PermissionError, OSError):
        # On Windows, SQLite files can be locked, ignore cleanup errors
        pass


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a database session for each test."""
    engine, database_url = test_db

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()


@pytest.fixture(scope="function", autouse=True)
def override_get_db(db_session):
    """Override the get_db dependency."""
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    yield
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def client(override_get_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
async def async_client(override_get_db):
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Test data fixtures
@pytest.fixture
def sample_channel_data():
    """Sample channel data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Channel",
        "group": "Test Group",
        "logo": "https://example.com/logo.png",
        "tvg_id": "test.channel",
        "tvg_name": "Test Channel",
        "source_url": "acestream://test123456789",
        "original_url": "http://example.com/playlist.m3u",
        "is_active": True,
        "is_online": True,
        "epg_update_protected": False
    }


@pytest.fixture
def sample_tv_channel_data():
    """Sample TV channel data for testing."""
    return {
        "name": "Test TV Channel",
        "description": "A test TV channel",
        "logo_url": "https://example.com/tv-logo.png",
        "category": "Entertainment",
        "country": "US",
        "language": "en",
        "website": "https://example.com",
        "epg_id": "test.tv",
        "channel_number": 1,
        "is_active": True,
        "is_favorite": False
    }


@pytest.fixture
def sample_epg_source_data():
    """Sample EPG source data for testing."""
    return {
        "url": "https://example.com/epg.xml",
        "name": "Test EPG Source",
        "enabled": True
    }


@pytest.fixture
def sample_scraped_url_data():
    """Sample scraped URL data for testing."""
    return {
        "url": "https://example.com/playlist.m3u",
        "url_type": "regular",
        "status": "active",
        "enabled": True
    }


@pytest.fixture
def sample_epg_program_data():
    """Sample EPG program data for testing."""
    return {
        "program_xml_id": "test-program-123",
        "title": "Test Program",
        "subtitle": "Test Episode",
        "description": "A test program for testing",
        "category": "Entertainment",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(hours=1),
        "image_url": "https://example.com/program.jpg"
    }


# Database seed fixtures
@pytest.fixture
def seed_channels(db_session, sample_channel_data):
    """Seed test channels."""
    channels = []
    channel_names = ["Alpha Channel", "Beta Channel", "Gamma Channel"]
    for i in range(3):
        channel_data = sample_channel_data.copy()
        channel_data["id"] = str(uuid.uuid4())
        channel_data["name"] = channel_names[i]
        channel_data["group"] = f"Group {i+1}"

        channel = AcestreamChannel(**channel_data)
        db_session.add(channel)
        channels.append(channel)

    db_session.commit()
    return channels


@pytest.fixture
def seed_tv_channels(db_session, sample_tv_channel_data):
    """Seed test TV channels."""
    tv_channels = []
    import time
    timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
    for i in range(3):
        tv_channel_data = sample_tv_channel_data.copy()
        tv_channel_data["name"] = f"Test TV Channel {i+1} {timestamp}"
        tv_channel_data["channel_number"] = i+1
        tv_channel_data["epg_id"] = f"test.tv.{i+1}.{timestamp}"  # Make EPG IDs unique too

        tv_channel = TVChannel(**tv_channel_data)
        db_session.add(tv_channel)
        tv_channels.append(tv_channel)

    db_session.commit()
    return tv_channels


@pytest.fixture
def seed_epg_sources(db_session, sample_epg_source_data):
    """Seed test EPG sources."""
    epg_sources = []
    for i in range(2):
        epg_source_data = sample_epg_source_data.copy()
        epg_source_data["name"] = f"Test EPG Source {i+1}"
        epg_source_data["url"] = f"https://example.com/epg{i+1}.xml"

        epg_source = EPGSource(**epg_source_data)
        db_session.add(epg_source)
        epg_sources.append(epg_source)

    db_session.commit()
    return epg_sources


@pytest.fixture
def seed_epg_channels(db_session, seed_epg_sources):
    """Seed test EPG channels."""
    epg_channels = []
    for i, epg_source in enumerate(seed_epg_sources):
        epg_channel_data = {
            "epg_source_id": epg_source.id,
            "channel_xml_id": f"test-channel-{i+1}",
            "name": f"Test EPG Channel {i+1}",
            "icon_url": f"https://example.com/icon{i+1}.png",
            "language": "en"
        }

        epg_channel = EPGChannel(**epg_channel_data)
        db_session.add(epg_channel)
        epg_channels.append(epg_channel)

    db_session.commit()
    return epg_channels


@pytest.fixture
def seed_epg_programs(db_session, seed_epg_channels, sample_epg_program_data):
    """Seed test EPG programs."""
    epg_programs = []
    for i, epg_channel in enumerate(seed_epg_channels):
        for j in range(3):  # 3 programs per channel
            program_data = sample_epg_program_data.copy()
            program_data["epg_channel_id"] = epg_channel.id
            program_data["program_xml_id"] = f"test-program-{i+1}-{j+1}"
            program_data["title"] = f"Test Program {i+1}-{j+1}"
            program_data["start_time"] = datetime.now() + timedelta(hours=j)
            program_data["end_time"] = datetime.now() + timedelta(hours=j+1)

            epg_program = EPGProgram(**program_data)
            db_session.add(epg_program)
            epg_programs.append(epg_program)

    db_session.commit()
    return epg_programs


@pytest.fixture
def seed_scraped_urls(db_session, sample_scraped_url_data):
    """Seed test scraped URLs."""
    scraped_urls = []
    for i in range(3):
        url_data = sample_scraped_url_data.copy()
        url_data["url"] = f"https://example.com/playlist{i+1}.m3u"

        scraped_url = ScrapedURL(**url_data)
        db_session.add(scraped_url)
        scraped_urls.append(scraped_url)

    db_session.commit()
    return scraped_urls

@pytest.fixture
def seed_all_data(seed_channels, seed_tv_channels, seed_epg_sources,
                  seed_epg_channels, seed_epg_programs, seed_scraped_urls):
    """Seed all test data."""
    return {
        "channels": seed_channels,
        "tv_channels": seed_tv_channels,
        "epg_sources": seed_epg_sources,
        "epg_channels": seed_epg_channels,
        "epg_programs": seed_epg_programs,
        "scraped_urls": seed_scraped_urls
    }


# Mock fixtures for external dependencies
@pytest.fixture
def mock_http_requests():
    """Mock HTTP requests for scrapers and search tests."""
    with patch('aiohttp.ClientSession') as mock_session:
        # Mock M3U playlist content
        mock_m3u_content = """#EXTM3U
#EXTINF:-1 tvg-id="test1" tvg-name="Alpha Channel" tvg-logo="https://example.com/logo1.png" group-title="Sports",Alpha Channel
acestream://abcdef123456789
#EXTINF:-1 tvg-id="test2" tvg-name="Beta Channel" tvg-logo="https://example.com/logo2.png" group-title="Movies",Beta Channel
acestream://fedcba987654321
"""

        # Mock response object
        async def mock_text():
            return mock_m3u_content

        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = mock_text
        mock_response.raise_for_status = Mock()

        # Mock async context manager for response
        async def mock_response_aenter(*args):
            return mock_response

        async def mock_response_aexit(*args):
            return None

        mock_response_cm = Mock()
        mock_response_cm.__aenter__ = mock_response_aenter
        mock_response_cm.__aexit__ = mock_response_aexit

        # Mock session instance
        mock_session_instance = Mock()
        mock_session_instance.get = Mock(return_value=mock_response_cm)

        # Mock async context manager for session
        async def mock_session_aenter(*args):
            return mock_session_instance

        async def mock_session_aexit(*args):
            return None

        mock_session_cm = Mock()
        mock_session_cm.__aenter__ = mock_session_aenter
        mock_session_cm.__aexit__ = mock_session_aexit

        mock_session.return_value = mock_session_cm

        yield mock_session

@pytest.fixture
def mock_acestream_search():
    """Mock Acestream search API."""
    with patch('app.services.search_service.requests.get') as mock_get:
        mock_search_response = {
            "result": {
                "results": [
                    {
                        "name": "Alpha Channel",
                        "items": [{
                            "infohash": "test-channel-1",
                            "categories": ["Sports"],
                            "bitrate": 1000
                        }]
                    }
                ],
                "total": 1
            }
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_search_response
        mock_response.text = json.dumps(mock_search_response)  # Return actual JSON string
        mock_get.return_value = mock_response
        yield mock_get


# Mock fixtures for external services
@pytest.fixture
def mock_acestream_engine():
    """Mock Acestream Engine API responses."""
    def _mock_engine_response(query="", page=0, page_size=10, category=""):
        # Return structured mock response matching the actual engine API
        if query == "":
            # Empty query returns all channels
            return {
                "result": {
                    "results": [
                        {
                            "name": "Sample Category",
                            "items": [
                                {
                                    "name": "Test Channel 1",
                                    "acestream_id": "test123456789",
                                    "category": "Entertainment",
                                    "group": "Test Group"
                                },
                                {
                                    "name": "Test Channel 2",
                                    "acestream_id": "test987654321",
                                    "category": "Sports",
                                    "group": "Sports Group"
                                }
                            ]
                        }
                    ],
                    "total": 2,
                    "page": page,
                    "page_size": page_size
                }
            }
        else:
            # Non-empty query returns filtered results
            return {
                "result": {
                    "results": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size
                }
            }

    return _mock_engine_response


@pytest.fixture
def mock_search_service(mock_acestream_engine):
    """Mock the search service to avoid external API calls."""
    with patch('requests.get') as mock_get:
        def _mock_requests_get(url, params=None, timeout=None):
            # Mock the requests.get call to the Acestream Engine
            mock_response = Mock()
            mock_response.status_code = 200

            # Get query parameters from the params
            query = params.get('query', '') if params else ''
            page = params.get('page', 0) if params else 0
            page_size = params.get('page_size', 10) if params else 10
            category = params.get('category', '') if params else ''

            # Generate mock response based on parameters
            mock_data = mock_acestream_engine(query, page, page_size, category)
            mock_response.json.return_value = mock_data
            mock_response.text = json.dumps(mock_data)

            return mock_response

        mock_get.side_effect = _mock_requests_get
        yield mock_get


@pytest.fixture
def mock_warp_service():
    """Mock WARP service to avoid external dependencies."""
    with patch('app.services.warp_service.WarpService') as mock_service:
        # Mock instance methods
        mock_instance = Mock()
        mock_instance.get_status.return_value = {
            "connected": False,
            "mode": "off",
            "account": None,
            "device": None
        }
        mock_instance.connect.return_value = {"success": True, "message": "Connected successfully"}
        mock_instance.disconnect.return_value = {"success": True, "message": "Disconnected successfully"}
        mock_instance.set_mode.return_value = {"success": True, "message": "Mode changed successfully"}

        mock_service.return_value = mock_instance
        yield mock_service


# Helper functions
def assert_channel_response(response_data, expected_data):
    """Assert that channel response matches expected data."""
    assert response_data["name"] == expected_data["name"]
    assert response_data["group"] == expected_data["group"]
    assert response_data["logo"] == expected_data["logo"]
    assert response_data["tvg_id"] == expected_data["tvg_id"]
    assert response_data["tvg_name"] == expected_data["tvg_name"]
    assert response_data["source_url"] == expected_data["source_url"]
    assert response_data["is_active"] == expected_data["is_active"]
    assert response_data["is_online"] == expected_data["is_online"]


def assert_tv_channel_response(response_data, expected_data):
    """Assert that TV channel response matches expected data."""
    assert response_data["name"] == expected_data["name"]
    assert response_data["description"] == expected_data["description"]
    assert response_data["logo_url"] == expected_data["logo_url"]
    assert response_data["category"] == expected_data["category"]
    assert response_data["country"] == expected_data["country"]
    assert response_data["language"] == expected_data["language"]
    assert response_data["website"] == expected_data["website"]
    assert response_data["epg_id"] == expected_data["epg_id"]
    assert response_data["channel_number"] == expected_data["channel_number"]
    assert response_data["is_active"] == expected_data["is_active"]
    assert response_data["is_favorite"] == expected_data["is_favorite"]


def assert_epg_source_response(response_data, expected_data):
    """Assert that EPG source response matches expected data."""
    assert response_data["name"] == expected_data["name"]
    assert response_data["url"] == expected_data["url"]
    assert response_data["enabled"] == expected_data["enabled"]


def assert_epg_channel_response(response_data, expected_data):
    """Assert that EPG channel response matches expected data."""
    assert response_data["channel_xml_id"] == expected_data["channel_xml_id"]
    assert response_data["name"] == expected_data["name"]
    assert response_data["icon_url"] == expected_data["icon_url"]
    assert response_data["language"] == expected_data["language"]


def assert_epg_program_response(response_data, expected_data):
    """Assert that EPG program response matches expected data."""
    assert response_data["program_xml_id"] == expected_data["program_xml_id"]
    assert response_data["title"] == expected_data["title"]
    assert response_data["subtitle"] == expected_data["subtitle"]
    assert response_data["description"] == expected_data["description"]
    assert response_data["category"] == expected_data["category"]
    assert response_data["image_url"] == expected_data["image_url"]

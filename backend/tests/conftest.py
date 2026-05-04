"""Shared fixtures for the V2 backend test suite.

Design note (post-B1 refactor): the previous version of this file cleared and
re-imported ``app.api``, ``app.models``, ``app.repositories``, ``app.schemas``,
``app.services``, ``app.tasks``, ``app.utils``, plus ``app.config.settings``,
``app.config.database``, and ``main`` once per fixture call. That worked for
settings/engine rebinding but came at a heavy cost: SQLAlchemy's declarative
``Base`` was reconstructed on every reload, splitting the mapper registry.
Test files that import ORM classes at module-import time held pre-reload class
objects whose registry could no longer resolve relationship names — the
``Mapper[TVChannel(tv_channels)] expression 'AcestreamChannel' failed to locate
a name`` crash documented in ``.planning/debug/epg-test-failure-domain.md``.

The runtime now binds the engine and session factory lazily (see
``app/config/database.py``) and the FastAPI startup hook lives in a
``lifespan`` context manager (see ``main.py``). That makes module reload
unnecessary: tests can override ``DATABASE_URL`` in the environment, clear
``get_settings``'s ``lru_cache``, and call ``reset_engine()`` to rebind the
runtime to a per-test database — without ever rebuilding ``Base`` or
recreating ORM classes. ``main`` and the model modules are imported exactly
once at conftest import time and reused by every fixture.
"""

import asyncio
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add v2/backend to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))


from migration_test_utils import database_url_for, upgrade_to_head

# Import the runtime ONCE. Never reloaded — that's the point of the refactor.
import main as _main_module  # noqa: E402
from app.config import database as _database_module  # noqa: E402
from app.config import settings as _settings_module  # noqa: E402


def _refresh_settings_cache():
    """Drop the ``get_settings`` ``lru_cache`` and refresh the module-level
    ``settings`` symbol so it reflects the current environment.
    """
    _settings_module.get_settings.cache_clear()
    _settings_module.settings = _settings_module.get_settings()


def _bind_runtime_to(database_url):
    """Bind the singleton runtime (``app``, engine, settings) to ``database_url``.

    ``database_url`` may be ``None`` to clear the override and fall back to
    whatever the default ``Settings.DATABASE_URL`` resolves to.
    """
    if database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = database_url

    _refresh_settings_cache()
    _database_module.reset_engine()


def _runtime_namespace():
    """Yield the back-compat namespace expected by existing fixtures and tests."""
    return SimpleNamespace(
        app=_main_module.app,
        get_db=_main_module.get_db,
        Base=_database_module.Base,
        engine=_database_module.get_engine(),
        SessionLocal=_database_module.SessionLocal,
        settings=_settings_module.settings,
    )


@pytest.fixture(scope="function")
def backend_runtime():
    """Yield the live FastAPI runtime bound to the default DB URL.

    Tests that need a per-test database override should depend on
    ``test_db`` / ``db_session`` (which create a separate engine and bind it
    via ``app.dependency_overrides``).
    """
    original = os.environ.get("DATABASE_URL")
    _bind_runtime_to(None)
    try:
        yield _runtime_namespace()
    finally:
        _bind_runtime_to(original)
        _database_module.reset_engine()


@pytest.fixture(scope="function")
def alembic_test_db():
    """Create a temp SQLite file and run Alembic to head against it."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    db_path = Path(db_path)

    upgrade_to_head(db_path)
    database_url = database_url_for(db_path)

    yield db_path, database_url

    try:
        os.unlink(db_path)
    except (PermissionError, OSError):
        pass


@pytest.fixture(scope="function")
def alembic_backend_runtime(alembic_test_db):
    """Yield the live runtime bound to a freshly-migrated per-test SQLite DB."""
    _, database_url = alembic_test_db
    original = os.environ.get("DATABASE_URL")
    _bind_runtime_to(database_url)

    expected_db_path = Path(database_url.removeprefix("sqlite:///"))
    assert Path(_database_module.get_engine().url.database).resolve() == expected_db_path.resolve()
    assert _settings_module.settings.DATABASE_URL == database_url

    try:
        yield _runtime_namespace()
    finally:
        _bind_runtime_to(original)
        _database_module.reset_engine()


# Test database setup
@pytest.fixture(scope="function")
def test_db(backend_runtime):
    """Create a temp SQLite engine using ``Base.metadata.create_all`` (legacy fast path)."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    database_url = f"sqlite:///{db_path}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    backend_runtime.Base.metadata.create_all(bind=engine)

    yield engine, database_url

    try:
        engine.dispose()
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


@pytest.fixture(scope="function")
def alembic_db_session(alembic_backend_runtime):
    """Create a migrated database session for each test."""
    session = alembic_backend_runtime.SessionLocal()

    yield session

    session.close()


def _seed_channels(session, sample_channel_data):
    from app.models.models import AcestreamChannel

    channels = []
    channel_names = ["Alpha Channel", "Beta Channel", "Gamma Channel"]
    for i in range(3):
        channel_data = sample_channel_data.copy()
        channel_data["id"] = str(uuid.uuid4())
        channel_data["name"] = channel_names[i]
        channel_data["group"] = f"Group {i+1}"

        channel = AcestreamChannel(**channel_data)
        session.add(channel)
        channels.append(channel)

    session.commit()
    return channels


def _seed_tv_channels(session, sample_tv_channel_data):
    from app.models.models import TVChannel

    tv_channels = []
    import time

    timestamp = int(time.time() * 1000)
    for i in range(3):
        tv_channel_data = sample_tv_channel_data.copy()
        tv_channel_data["name"] = f"Test TV Channel {i+1} {timestamp}"
        tv_channel_data["channel_number"] = i+1
        tv_channel_data["epg_id"] = f"test.tv.{i+1}.{timestamp}"

        tv_channel = TVChannel(**tv_channel_data)
        session.add(tv_channel)
        tv_channels.append(tv_channel)

    session.commit()
    return tv_channels


def _seed_epg_sources(session, sample_epg_source_data):
    from app.models.models import EPGSource

    epg_sources = []
    for i in range(2):
        epg_source_data = sample_epg_source_data.copy()
        epg_source_data["name"] = f"Test EPG Source {i+1}"
        epg_source_data["url"] = f"https://example.com/epg{i+1}.xml"

        epg_source = EPGSource(**epg_source_data)
        session.add(epg_source)
        epg_sources.append(epg_source)

    session.commit()
    return epg_sources


def _seed_epg_channels(session, epg_sources):
    from app.models.models import EPGChannel

    epg_channels = []
    for i, epg_source in enumerate(epg_sources):
        epg_channel_data = {
            "epg_source_id": epg_source.id,
            "channel_xml_id": f"test-channel-{i+1}",
            "name": f"Test EPG Channel {i+1}",
            "icon_url": f"https://example.com/icon{i+1}.png",
            "language": "en",
        }

        epg_channel = EPGChannel(**epg_channel_data)
        session.add(epg_channel)
        epg_channels.append(epg_channel)

    session.commit()
    return epg_channels


def _seed_epg_programs(session, epg_channels, sample_epg_program_data):
    from app.models.models import EPGProgram

    epg_programs = []
    for i, epg_channel in enumerate(epg_channels):
        for j in range(3):
            program_data = sample_epg_program_data.copy()
            program_data["epg_channel_id"] = epg_channel.id
            program_data["program_xml_id"] = f"test-program-{i+1}-{j+1}"
            program_data["title"] = f"Test Program {i+1}-{j+1}"
            program_data["start_time"] = datetime.now() + timedelta(hours=j)
            program_data["end_time"] = datetime.now() + timedelta(hours=j+1)

            epg_program = EPGProgram(**program_data)
            session.add(epg_program)
            epg_programs.append(epg_program)

    session.commit()
    return epg_programs


def _seed_scraped_urls(session, sample_scraped_url_data):
    from app.models.models import ScrapedURL

    scraped_urls = []
    for i in range(3):
        url_data = sample_scraped_url_data.copy()
        url_data["url"] = f"https://example.com/playlist{i+1}.m3u"

        scraped_url = ScrapedURL(**url_data)
        session.add(scraped_url)
        scraped_urls.append(scraped_url)

    session.commit()
    return scraped_urls


@pytest.fixture(scope="function")
def override_get_db(backend_runtime, db_session):
    """Override the get_db dependency."""
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    backend_runtime.app.dependency_overrides[backend_runtime.get_db] = _get_db_override
    yield
    del backend_runtime.app.dependency_overrides[backend_runtime.get_db]


@pytest.fixture(scope="function")
def alembic_override_get_db(alembic_backend_runtime, alembic_db_session):
    """Override the migrated app database dependency."""
    def _get_db_override():
        try:
            yield alembic_db_session
        finally:
            pass

    alembic_backend_runtime.app.dependency_overrides[alembic_backend_runtime.get_db] = _get_db_override
    yield
    del alembic_backend_runtime.app.dependency_overrides[alembic_backend_runtime.get_db]


@pytest.fixture(scope="function")
def client(backend_runtime, override_get_db):
    """Create a test client."""
    return TestClient(backend_runtime.app)


@pytest.fixture(scope="function")
def alembic_client(alembic_backend_runtime, alembic_override_get_db):
    """Create a migrated test client."""
    return TestClient(alembic_backend_runtime.app)


@pytest.fixture(scope="function")
async def async_client(backend_runtime, override_get_db):
    """Create an async test client."""
    async with AsyncClient(app=backend_runtime.app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def alembic_async_client(alembic_backend_runtime, alembic_override_get_db):
    """Create an async migrated test client."""
    async with AsyncClient(app=alembic_backend_runtime.app, base_url="http://test") as ac:
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
    return _seed_channels(db_session, sample_channel_data)


@pytest.fixture
def seed_tv_channels(db_session, sample_tv_channel_data):
    """Seed test TV channels."""
    return _seed_tv_channels(db_session, sample_tv_channel_data)


@pytest.fixture
def seed_epg_sources(db_session, sample_epg_source_data):
    """Seed test EPG sources."""
    return _seed_epg_sources(db_session, sample_epg_source_data)


@pytest.fixture
def seed_epg_channels(db_session, seed_epg_sources):
    """Seed test EPG channels."""
    return _seed_epg_channels(db_session, seed_epg_sources)


@pytest.fixture
def seed_epg_programs(db_session, seed_epg_channels, sample_epg_program_data):
    """Seed test EPG programs."""
    return _seed_epg_programs(db_session, seed_epg_channels, sample_epg_program_data)


@pytest.fixture
def seed_scraped_urls(db_session, sample_scraped_url_data):
    """Seed test scraped URLs."""
    return _seed_scraped_urls(db_session, sample_scraped_url_data)

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


@pytest.fixture
def alembic_seed_all_data(
    alembic_db_session,
    sample_channel_data,
    sample_tv_channel_data,
    sample_epg_source_data,
    sample_scraped_url_data,
    sample_epg_program_data,
):
    """Seed the Alembic-backed Task 5 subset without constructing the legacy DB path."""
    channels = _seed_channels(alembic_db_session, sample_channel_data)
    tv_channels = _seed_tv_channels(alembic_db_session, sample_tv_channel_data)
    epg_sources = _seed_epg_sources(alembic_db_session, sample_epg_source_data)
    epg_channels = _seed_epg_channels(alembic_db_session, epg_sources)
    epg_programs = _seed_epg_programs(alembic_db_session, epg_channels, sample_epg_program_data)
    scraped_urls = _seed_scraped_urls(alembic_db_session, sample_scraped_url_data)

    return {
        "channels": channels,
        "tv_channels": tv_channels,
        "epg_sources": epg_sources,
        "epg_channels": epg_channels,
        "epg_programs": epg_programs,
        "scraped_urls": scraped_urls,
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

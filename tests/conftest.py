import pytest
from flask import Flask, _app_ctx_stack
from flask.testing import FlaskClient
from unittest.mock import MagicMock, AsyncMock
from app import create_app
from app.extensions import db
from app.models import ScrapedURL, AcestreamChannel
from app.utils.config import Config
import sqlalchemy
import os
from app.repositories import SettingsRepository
from pathlib import Path
import tempfile
import logging

# Set up logging to debug database issues
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('sqlalchemy.engine')
logger.setLevel(logging.INFO)

# Reset any singleton instances between tests
@pytest.fixture(autouse=True, scope="function")
def reset_singletons():
    """Reset singleton instances between tests."""
    if hasattr(Config, '_instance') and Config._instance is not None:
        Config._instance = None
    yield

@pytest.fixture(scope='function')
def reset_config():
    """Reset Config singleton between tests."""
    # Save the original instance
    original_instance = Config._instance if hasattr(Config, '_instance') else None
    # Reset the instance
    Config._instance = None
    yield
    # Restore the original instance after the test
    Config._instance = original_instance

@pytest.fixture(scope='function')
def app():
    """Create application for the tests."""
    # Set testing environment
    os.environ['TESTING'] = '1'
    
    # Create base app without initialization
    app = Flask(__name__)
    
    # Configure SQLite in-memory database
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'PRESERVE_CONTEXT_ON_EXCEPTION': False
    })
    
    # Initialize database
    db.init_app(app)
    
    # Create tables within app context
    with app.app_context():
        db.create_all()
        
        # Initialize settings for testing
        from app.repositories import SettingsRepository
        settings_repo = SettingsRepository()
        settings_repo.set('setup_completed', 'True')
        db.session.commit()
    
    # Now create the full application
    app = create_app('testing')
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'PRESERVE_CONTEXT_ON_EXCEPTION': False
    })
    
    yield app
    
    # Clean up environment
    os.environ.pop('TESTING', None)

@pytest.fixture
def client(app, db_session):
    """Create Flask test client with initialized database."""
    with app.test_client() as test_client:
        with app.app_context():
            yield test_client

@pytest.fixture
def app_context(app):
    """Create an application context for tests."""
    with app.app_context() as ctx:
        yield ctx
        # Don't pop the context here - let the test manage it

@pytest.fixture
def db_session(app):
    """Set up the database and create tables."""
    with app.app_context():
        # Explicitly create tables
        db.create_all()
        
        # Log created tables
        print(f"Created tables: {db.engine.table_names()}")
        
        yield db.session
        
        # Clean up
        db.session.close()
        db.drop_all()

@pytest.fixture(autouse=True)
def reset_db(db_session):
    """Reset database after each test."""
    yield
    # Clear database tables after test 
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

@pytest.fixture
def mock_settings_repo():
    """Create a mock settings repository."""
    repo = MagicMock()
    repo.is_setup_completed.return_value = True
    
    # Mock the get method with specific returns for different keys
    def mock_get(key, default=None):
        settings = {
            "base_url": "http://localhost:6878/ace/getstream?id=",
            "ace_engine_url": "http://localhost:6878",
            "rescrape_interval": 24
        }
        return settings.get(key, default)
    
    repo.get.side_effect = mock_get
    return repo

@pytest.fixture
def config():
    """Provide a properly configured Config instance for tests."""
    # Reset singleton
    if hasattr(Config, '_instance'):
        Config._instance = None
    
    # Create fresh config instance
    config = Config()
    
    # Set test database path to a temporary file
    config.config_path = Path(tempfile.gettempdir())
    config.database_path = config.config_path / 'test_acestream.db'
    
    # Ensure required attributes exist
    config.base_url = "http://localhost:6878/ace/getstream?id="
    config.ace_engine_url = "http://localhost:6878"
    config.rescrape_interval = 24
    
    return config

@pytest.fixture(autouse=True)
def override_setup_check(monkeypatch):
    """Override setup check to always return True for tests."""
    def is_initialized(self):  # Add 'self' parameter here
        return True
        
    monkeypatch.setattr('app.utils.config.Config.is_initialized', is_initialized)

@pytest.fixture
def settings_repo(app):
    """Create settings repository for tests."""
    from app.repositories import SettingsRepository
    repo = SettingsRepository()
    repo.setup_defaults()
    repo.mark_setup_completed()
    return repo

@pytest.fixture(autouse=True)
def mock_task_manager(monkeypatch):
    """Mock task manager for testing."""
    mock_manager = MagicMock()
    mock_manager.process_url = AsyncMock()
    mock_manager.add_task = AsyncMock()
    
    # Patch the controller level
    monkeypatch.setattr('app.api.controllers.urls_controller.task_manager', mock_manager)
    
    return mock_manager

@pytest.fixture(autouse=True)
def setup_task_manager(app, monkeypatch):
    """Set up task manager for testing."""
    from app.tasks.manager import TaskManager
    
    # Create a task manager instance for testing
    task_manager = TaskManager()
    task_manager.init_app(app)
    
    # Mock the process_url method to be synchronous for testing
    async def mock_process_url(url):
        return True
    
    task_manager.process_url = mock_process_url
    
    # Make this task manager instance available to the app
    monkeypatch.setattr('app.api.controllers.urls_controller.task_manager', task_manager)
    
    return task_manager

# Fix the clean_app_contexts fixture
@pytest.fixture(autouse=True)
def clean_app_contexts():
    """Clean up any leftover app contexts after tests."""
    yield
    # Clean up any lingering app contexts that weren't properly popped
    while hasattr(_app_ctx_stack, "top") and _app_ctx_stack.top is not None:
        _app_ctx_stack.top.pop()

@pytest.fixture
def setup_test_channels(db_session):
    """Set up test channels for tests."""
    # Create test channels with correct attribute name (id not channel_id)
    ch1 = AcestreamChannel(
        id='123', 
        name='Sports Channel', 
        group='Sports', 
        logo='sports.png', 
        is_online=True,
        status='active'
    )
    ch2 = AcestreamChannel(
        id='456', 
        name='News Channel', 
        group='News', 
        logo='news.png', 
        is_online=True,
        status='active'
    )
    db_session.add_all([ch1, ch2])
    db_session.commit()
    return [ch1, ch2]
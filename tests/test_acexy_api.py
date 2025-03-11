import pytest
from unittest.mock import patch, MagicMock
import json
import requests
from flask import Flask, Blueprint
from app.extensions import db

@pytest.fixture
def app():
    """Create a Flask test app."""
    # Use the blueprint and API from app.api instead of trying to import create_app
    from app.api import bp, api
    app = Flask(__name__)
    
    # Configure the app properly for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Explicitly disable to avoid warning
    app.config['TESTING'] = True
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Register blueprint
    app.register_blueprint(bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    with app.test_client() as client:
        with app.app_context():
            yield client

class TestAcexyStatus:
    
    @patch('requests.get')
    def test_acexy_status_available(self, mock_get, client, app):
        """Test Acexy status when available."""
        # Mock the response from Acexy
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        # Set config to use Acexy
        with app.app_context():
            with patch('os.environ.get', return_value='true'):
                with patch('app.api.controllers.config_controller.Config') as mock_config:
                    config_instance = mock_config.return_value
                    config_instance.get.return_value = 'http://localhost:8080'
                    
                    response = client.get('/api/config/acexy_status')
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data['enabled'] is True
                    assert data['available'] is True
            
    @patch('requests.get')
    def test_acexy_status_unavailable(self, mock_get, client, app):
        """Test Acexy status when enabled but unavailable."""
        # Mock the response from Acexy - fails
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        # Set config to use Acexy
        with app.app_context():
            with patch('os.environ.get', return_value='true'):
                with patch('app.api.controllers.config_controller.Config') as mock_config:
                    config_instance = mock_config.return_value
                    config_instance.get.return_value = 'http://localhost:8080'
                    
                    response = client.get('/api/config/acexy_status')
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data['enabled'] is True
                    assert data['available'] is False
            
    def test_acexy_status_disabled(self, client, app):
        """Test Acexy status when not enabled."""
        # Set config to not use Acexy (environment variable is false)
        with app.app_context():
            with patch('os.environ.get', return_value='false'):
                response = client.get('/api/config/acexy_status')
                data = json.loads(response.data)
                
                assert response.status_code == 200
                assert data['enabled'] is False

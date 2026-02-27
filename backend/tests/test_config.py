"""
Integration tests for Config endpoints
"""

import pytest
from fastapi import status


class TestConfigEndpoints:
    """Test configuration management endpoints."""

    def test_get_base_url_default(self, client):
        """Test getting base URL setting (default value)."""
        response = client.get("/api/v1/config/base_url")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "value" in data
        # Should have a default value
        assert data["value"] is not None

    def test_update_base_url(self, client):
        """Test updating base URL setting."""
        new_base_url = "http://new-server.example.com:8000"
        update_data = {"base_url": new_base_url}

        response = client.put("/api/v1/config/base_url", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Base URL updated successfully"

        # Verify the setting was updated
        response = client.get("/api/v1/config/base_url")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == new_base_url

    def test_update_base_url_invalid_format(self, client):
        """Test updating base URL with invalid format."""
        invalid_url = "not-a-valid-url"
        update_data = {"value": invalid_url}

        response = client.put("/api/v1/config/base_url", json=update_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_ace_engine_url_default(self, client):
        """Test getting acestream engine URL setting."""
        response = client.get("/api/v1/config/ace_engine_url")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "key" in data
        assert "value" in data
        assert data["key"] == "ace_engine_url"

    def test_update_ace_engine_url(self, client):
        """Test updating acestream engine URL setting."""
        new_engine_url = "http://acestream-engine.example.com:6878"
        update_data = {"value": new_engine_url}

        response = client.put("/api/v1/config/ace_engine_url", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Setting updated successfully"

        # Verify the setting was updated
        response = client.get("/api/v1/config/ace_engine_url")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == new_engine_url

    def test_get_rescrape_interval_default(self, client):
        """Test getting rescrape interval setting."""
        response = client.get("/api/v1/config/rescrape_interval")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "key" in data
        assert "value" in data
        assert data["key"] == "rescrape_interval"
        # Should be a numeric value
        assert isinstance(int(data["value"]), int)

    def test_update_rescrape_interval(self, client):
        """Test updating rescrape interval setting."""
        new_interval = "7200"  # 2 hours
        update_data = {"value": new_interval}

        response = client.put("/api/v1/config/rescrape_interval", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Setting updated successfully"

        # Verify the setting was updated
        response = client.get("/api/v1/config/rescrape_interval")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == new_interval

    def test_update_rescrape_interval_invalid_value(self, client):
        """Test updating rescrape interval with invalid value."""
        invalid_interval = "not-a-number"
        update_data = {"value": invalid_interval}

        response = client.put("/api/v1/config/rescrape_interval", json=update_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_rescrape_interval_negative_value(self, client):
        """Test updating rescrape interval with negative value."""
        negative_interval = "-3600"
        update_data = {"value": negative_interval}

        response = client.put("/api/v1/config/rescrape_interval", json=update_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_addpid_setting_default(self, client):
        """Test getting addpid setting."""
        response = client.get("/api/v1/config/addpid")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "key" in data
        assert "value" in data
        assert data["key"] == "addpid"
        # Should be a boolean value (as string)
        assert data["value"] in ["true", "false", "True", "False", "0", "1"]

    def test_update_addpid_setting(self, client):
        """Test updating addpid setting."""
        new_addpid = "true"
        update_data = {"value": new_addpid}

        response = client.put("/api/v1/config/addpid", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Setting updated successfully"

        # Verify the setting was updated
        response = client.get("/api/v1/config/addpid")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == new_addpid

    def test_update_addpid_setting_boolean_values(self, client):
        """Test updating addpid setting with different boolean values."""
        boolean_values = ["true", "false", "True", "False", "1", "0"]

        for value in boolean_values:
            update_data = {"value": value}
            response = client.put("/api/v1/config/addpid", json=update_data)
            assert response.status_code == status.HTTP_200_OK

            # Verify the setting was updated
            response = client.get("/api/v1/config/addpid")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["value"] == value


class TestConfigAllSettingsEndpoint:
    """Test the all settings endpoint."""

    def test_get_all_settings(self, client):
        """Test getting all configuration settings."""
        response = client.get("/api/v1/config/all")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "settings" in data

        settings = data["settings"]
        assert isinstance(settings, dict)

        # Should contain all the main settings
        expected_keys = ["base_url", "ace_engine_url", "rescrape_interval", "addpid"]
        for key in expected_keys:
            assert key in settings
            assert isinstance(settings[key], str)

    def test_get_all_settings_structure(self, client):
        """Test the structure of all settings response."""
        response = client.get("/api/v1/config/all")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "settings" in data
        assert isinstance(data["settings"], dict)

        # Each setting should be a string value
        for key, value in data["settings"].items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    def test_get_all_settings_after_updates(self, client):
        """Test getting all settings after making updates."""
        # Update several settings
        updates = [
            ("base_url", "http://updated.example.com"),
            ("ace_engine_url", "http://engine.example.com:6878"),
            ("rescrape_interval", "3600"),
            ("addpid", "true")
        ]

        for key, value in updates:
            update_data = {"value": value}
            response = client.put(f"/api/v1/config/{key}", json=update_data)
            assert response.status_code == status.HTTP_200_OK

        # Get all settings
        response = client.get("/api/v1/config/all")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify all updates are reflected
        settings = data["settings"]
        for key, expected_value in updates:
            assert settings[key] == expected_value


class TestConfigAcestreamStatusEndpoint:
    """Test acestream status endpoint."""

    def test_get_acestream_status(self, client):
        """Test getting acestream engine status."""
        response = client.get("/api/v1/config/acestream_status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should contain status information
        assert "status" in data
        assert "engine_url" in data
        assert "accessible" in data

        # Status should be a string
        assert isinstance(data["status"], str)
        assert isinstance(data["engine_url"], str)
        assert isinstance(data["accessible"], bool)

    def test_acestream_status_with_custom_engine_url(self, client):
        """Test acestream status with custom engine URL."""
        # Set custom engine URL
        custom_url = "http://custom-engine.example.com:6878"
        update_data = {"value": custom_url}
        response = client.put("/api/v1/config/ace_engine_url", json=update_data)
        assert response.status_code == status.HTTP_200_OK

        # Check status
        response = client.get("/api/v1/config/acestream_status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should use the custom URL
        assert data["engine_url"] == custom_url

    def test_acestream_status_error_handling(self, client):
        """Test acestream status error handling."""
        # Set invalid engine URL
        invalid_url = "http://nonexistent.example.com:9999"
        update_data = {"value": invalid_url}
        response = client.put("/api/v1/config/ace_engine_url", json=update_data)
        assert response.status_code == status.HTTP_200_OK

        # Check status (should handle connection errors gracefully)
        response = client.get("/api/v1/config/acestream_status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should indicate engine is not accessible
        assert data["accessible"] == False
        assert "error" in data["status"] or "unreachable" in data["status"].lower()


class TestConfigIntegration:
    """Test config integration with other components."""

    def test_config_persistence(self, client, db_session):
        """Test that configuration changes persist."""
        # Update a setting
        new_value = "http://persistent.example.com"
        update_data = {"value": new_value}
        response = client.put("/api/v1/config/base_url", json=update_data)
        assert response.status_code == status.HTTP_200_OK

        # Commit the transaction
        db_session.commit()

        # Get the setting again
        response = client.get("/api/v1/config/base_url")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == new_value

    def test_config_validation_integration(self, client):
        """Test config validation across different endpoints."""
        # Test URL validation
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "http://",
            ""
        ]

        for invalid_url in invalid_urls:
            update_data = {"value": invalid_url}
            response = client.put("/api/v1/config/base_url", json=update_data)
            # Should reject invalid URLs
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test numeric validation
        invalid_intervals = [
            "not-a-number",
            "-1",
            "0",
            "abc123"
        ]

        for invalid_interval in invalid_intervals:
            update_data = {"value": invalid_interval}
            response = client.put("/api/v1/config/rescrape_interval", json=update_data)
            # Should reject invalid intervals
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_config_defaults_initialization(self, client):
        """Test that config endpoints have sensible defaults."""
        config_endpoints = [
            "base_url",
            "ace_engine_url",
            "rescrape_interval",
            "addpid"
        ]

        for endpoint in config_endpoints:
            response = client.get(f"/api/v1/config/{endpoint}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["key"] == endpoint
            assert data["value"] is not None
            assert data["value"] != ""

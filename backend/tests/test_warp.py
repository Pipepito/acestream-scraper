"""
Integration tests for WARP endpoints
"""

import pytest
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

# Patch the warp_service instance in the endpoint module, not the class
WARP_CONNECT_PATH = 'app.api.endpoints.warp.warp_service.connect'
WARP_DISCONNECT_PATH = 'app.api.endpoints.warp.warp_service.disconnect'
WARP_SET_MODE_PATH = 'app.api.endpoints.warp.warp_service.set_mode'
WARP_GET_STATUS_PATH = 'app.api.endpoints.warp.warp_service.get_status'
WARP_REGISTER_LICENSE_PATH = 'app.api.endpoints.warp.warp_service.register_license'


class TestWARPStatusEndpoint:
    """Test WARP status endpoint."""

    @patch(WARP_GET_STATUS_PATH, new_callable=AsyncMock)
    def test_get_warp_status_disconnected(self, mock_get_status, client):
        """Test getting WARP status when disconnected."""
        mock_get_status.return_value = {
            "connected": False,
            "mode": "off",
            "account_type": "free",
            "license": None
        }

        response = client.get("/api/v1/warp/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "connected" in data
        assert "mode" in data
        assert "account_type" in data
        assert data["connected"] == False
        assert data["mode"] == "off"
        assert data["account_type"] == "free"

    @patch(WARP_GET_STATUS_PATH, new_callable=AsyncMock)
    def test_get_warp_status_connected(self, mock_get_status, client):
        """Test getting WARP status when connected."""
        mock_get_status.return_value = {
            "running": True,
            "connected": True,
            "mode": "warp",
            "account_type": "premium",
            "ip": "192.168.1.100",
            "cf_trace": {"colo": "DFW"}
        }

        response = client.get("/api/v1/warp/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["connected"] == True
        assert data["mode"] == "warp"
        assert data["account_type"] == "premium"
        assert "ip" in data
        assert "cf_trace" in data

    @patch(WARP_GET_STATUS_PATH, new_callable=AsyncMock)
    def test_get_warp_status_error(self, mock_get_status, client):
        """Test getting WARP status when service has error."""
        mock_get_status.side_effect = Exception("WARP service not available")

        # When the service raises an exception, FastAPI will return 500
        response = client.get("/api/v1/warp/status")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "Internal Server Error" in data["detail"]


class TestWARPConnectionEndpoints:
    """Test WARP connection/disconnection endpoints."""

    @patch(WARP_CONNECT_PATH, new_callable=AsyncMock)
    def test_connect_warp_success(self, mock_connect, client):
        """Test successful WARP connection."""
        # Ensure return_value is a plain dict, not a coroutine
        mock_connect.return_value = {
            "success": True,
            "message": "Connected to WARP successfully",
            "status": {
                "connected": True,
                "mode": "warp",
                "endpoint": "warp.cloudflare.com"
            }
        }
        response = client.post("/api/v1/warp/connect")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == True
        assert "message" in data
        assert "status" in data
        assert data["status"]["connected"] == True

    @patch(WARP_CONNECT_PATH, new_callable=AsyncMock)
    def test_connect_warp_failure(self, mock_connect, client):
        """Test failed WARP connection."""
        # Ensure return_value is a plain dict, not a coroutine
        mock_connect.return_value = {
            "success": False,
            "message": "Failed to connect to WARP",
            "error": "WARP daemon not running"
        }
        response = client.post("/api/v1/warp/connect")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] == False
        assert "message" in data
        assert "error" in data

    @patch(WARP_CONNECT_PATH, new_callable=AsyncMock)
    def test_connect_warp_with_mode(self, mock_connect, client):
        """Test WARP connection with specific mode."""
        mock_connect.return_value = {
            "success": True,
            "message": "Connected to WARP in DoT mode",
            "status": {
                "connected": True,
                "mode": "dot"
            }
        }

        request_data = {"mode": "dot"}
        response = client.post("/api/v1/warp/connect", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] == True
        assert data["status"]["mode"] == "dot"
        # Verify the service was called with the mode
        mock_connect.assert_called_once_with(mode="dot")

    @patch(WARP_DISCONNECT_PATH, new_callable=AsyncMock)
    def test_disconnect_warp_success(self, mock_disconnect, client):
        """Test successful WARP disconnection."""
        mock_disconnect.return_value = {
            "success": True,
            "message": "Disconnected from WARP successfully",
            "status": {
                "connected": False,
                "mode": "off"
            }
        }

        response = client.post("/api/v1/warp/disconnect")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] == True
        assert "message" in data
        assert "status" in data
        assert data["status"]["connected"] == False

    @patch(WARP_DISCONNECT_PATH, new_callable=AsyncMock)
    def test_disconnect_warp_failure(self, mock_disconnect, client):
        """Test failed WARP disconnection."""
        mock_disconnect.return_value = {
            "success": False,
            "message": "Failed to disconnect from WARP",
            "error": "No active WARP connection"
        }

        response = client.post("/api/v1/warp/disconnect")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()

        assert data["success"] == False
        assert "message" in data
        assert "error" in data


class TestWARPModeEndpoint:
    """Test WARP mode switching endpoint."""

    @patch(WARP_SET_MODE_PATH, new_callable=AsyncMock)
    def test_set_warp_mode_warp(self, mock_set_mode, client):
        """Test setting WARP mode to 'warp'."""
        mock_set_mode.return_value = {
            "success": True,
            "message": "WARP mode set to warp",
            "status": {
                "connected": True,
                "mode": "warp"
            }
        }

        request_data = {"mode": "warp"}
        response = client.post("/api/v1/warp/mode", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] == True
        assert data["status"]["mode"] == "warp"
        mock_set_mode.assert_called_once_with("warp")

    @patch(WARP_SET_MODE_PATH, new_callable=AsyncMock)
    def test_set_warp_mode_dot(self, mock_set_mode, client):
        """Test setting WARP mode to 'dot'."""
        mock_set_mode.return_value = {
            "success": True,
            "message": "WARP mode set to dot",
            "status": {
                "connected": True,
                "mode": "dot"
            }
        }

        request_data = {"mode": "dot"}
        response = client.post("/api/v1/warp/mode", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] == True
        assert data["status"]["mode"] == "dot"

    @patch(WARP_SET_MODE_PATH, new_callable=AsyncMock)
    def test_set_warp_mode_proxy(self, mock_set_mode, client):
        """Test setting WARP mode to 'proxy'."""
        mock_set_mode.return_value = {
            "success": True,
            "message": "WARP mode set to proxy",
            "status": {
                "connected": True,
                "mode": "proxy"
            }
        }

        request_data = {"mode": "proxy"}
        response = client.post("/api/v1/warp/mode", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] == True
        assert data["status"]["mode"] == "proxy"

    @patch(WARP_SET_MODE_PATH, new_callable=AsyncMock)
    def test_set_warp_mode_invalid(self, mock_set_mode, client):
        """Test setting invalid WARP mode."""
        request_data = {"mode": "invalid_mode"}
        response = client.post("/api/v1/warp/mode", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch(WARP_SET_MODE_PATH, new_callable=AsyncMock)
    def test_set_warp_mode_missing_data(self, mock_set_mode, client):
        """Test setting WARP mode without mode parameter."""
        response = client.post("/api/v1/warp/mode", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch(WARP_SET_MODE_PATH, new_callable=AsyncMock)
    def test_set_warp_mode_failure(self, mock_set_mode, client):
        """Test failed WARP mode change."""
        mock_set_mode.return_value = {
            "success": False,
            "message": "Failed to change WARP mode",
            "error": "WARP not connected"
        }

        request_data = {"mode": "warp"}
        response = client.post("/api/v1/warp/mode", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()

        assert data["success"] == False
        assert "error" in data


class TestWARPLicenseEndpoint:
    """Test WARP license registration endpoint."""

    @patch(WARP_REGISTER_LICENSE_PATH, new_callable=AsyncMock)
    def test_register_warp_license_success(self, mock_register_license, client):
        """Test successful WARP license registration."""
        mock_register_license.return_value = {
            "success": True,
            "message": "License registered successfully",
            "account_type": "premium",
            "license": "test-premium-license"
        }

        request_data = {"license": "test-premium-license"}
        response = client.post("/api/v1/warp/license", json=request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] == True
        assert "message" in data
        assert data["account_type"] == "premium"
        assert data["license"] == "test-premium-license"
        mock_register_license.assert_called_once_with("test-premium-license")

    @patch(WARP_REGISTER_LICENSE_PATH, new_callable=AsyncMock)
    def test_register_warp_license_invalid(self, mock_register_license, client):
        """Test registering invalid WARP license."""
        mock_register_license.return_value = {
            "success": False,
            "message": "Invalid license key",
            "error": "License key format is invalid"
        }

        request_data = {"license": "invalid-license"}
        response = client.post("/api/v1/warp/license", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()

        assert data["success"] == False
        assert "error" in data

    @patch(WARP_REGISTER_LICENSE_PATH, new_callable=AsyncMock)
    def test_register_warp_license_missing_data(self, mock_register_license, client):
        """Test registering WARP license without license parameter."""
        response = client.post("/api/v1/warp/license", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch(WARP_REGISTER_LICENSE_PATH, new_callable=AsyncMock)
    def test_register_warp_license_empty_license(self, mock_register_license, client):
        """Test registering WARP license with empty license."""
        request_data = {"license": ""}
        response = client.post("/api/v1/warp/license", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch(WARP_REGISTER_LICENSE_PATH, new_callable=AsyncMock)
    def test_register_warp_license_already_registered(self, mock_register_license, client):
        """Test registering WARP license when already registered."""
        mock_register_license.return_value = {
            "success": False,
            "message": "License already registered",
            "error": "A license is already active on this device"
        }

        request_data = {"license": "already-registered-license"}
        response = client.post("/api/v1/warp/license", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()

        assert data["success"] == False
        assert "error" in data


class TestWARPEndpointIntegration:
    """Test WARP endpoint integration and workflows."""

    @patch(WARP_GET_STATUS_PATH, new_callable=AsyncMock)
    @patch(WARP_CONNECT_PATH, new_callable=AsyncMock)
    @patch(WARP_DISCONNECT_PATH, new_callable=AsyncMock)
    def test_warp_connection_workflow(self, mock_disconnect, mock_connect, mock_get_status, client):
        # Ensure return_value is a plain dict, not a coroutine
        mock_connect.return_value = {
            "success": True,
            "message": "Connected to WARP successfully",
            "status": {
                "connected": True,
                "mode": "warp",
                "endpoint": "warp.cloudflare.com"
            }
        }
        mock_get_status.return_value = {
            "connected": True,
            "mode": "warp",
            "account_type": "premium",
            "ip": "192.168.1.100",
            "cf_trace": {"colo": "DFW"}
        }
        response = client.get("/api/v1/warp/status")
        assert response.status_code == status.HTTP_200_OK
        response = client.post("/api/v1/warp/connect")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == True
        assert data["status"]["connected"] == True

        # Disconnect from WARP
        mock_disconnect.return_value = {
            "success": True,
            "message": "Disconnected from WARP successfully",
            "status": {
                "connected": False,
                "mode": "off"
            }
        }

        response = client.post("/api/v1/warp/disconnect")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == True
        assert data["status"]["connected"] == False

    @patch(WARP_REGISTER_LICENSE_PATH, new_callable=AsyncMock)
    @patch(WARP_GET_STATUS_PATH, new_callable=AsyncMock)
    def test_warp_license_and_status_integration(self, mock_get_status, mock_register_license, client):
        """Test WARP license registration and status integration."""
        # Register premium license
        mock_register_license.return_value = {
            "success": True,
            "message": "License registered",
            "account_type": "premium",
            "license": "premium-license"
        }

        response = client.post("/api/v1/warp/license", json={"license": "premium-license"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["account_type"] == "premium"

        # Check status reflects premium account
        mock_get_status.return_value = {
            "connected": False,
            "mode": "off",
            "account_type": "premium",
            "license": "premium-license"
        }

        response = client.get("/api/v1/warp/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["account_type"] == "premium"
        assert data["license"] == "premium-license"

    @patch(WARP_SET_MODE_PATH, new_callable=AsyncMock)
    @patch(WARP_CONNECT_PATH, new_callable=AsyncMock)
    def test_warp_mode_switching_integration(self, mock_connect, mock_set_mode, client):
        """Test WARP mode switching integration."""
        # Connect in warp mode
        mock_connect.return_value = {
            "success": True,
            "message": "Connected in warp mode",
            "status": {"connected": True, "mode": "warp"}
        }

        response = client.post("/api/v1/warp/connect", json={"mode": "warp"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"]["mode"] == "warp"

        # Switch to DoT mode
        mock_set_mode.return_value = {
            "success": True,
            "message": "Mode changed to dot",
            "status": {"connected": True, "mode": "dot"}
        }

        response = client.post("/api/v1/warp/mode", json={"mode": "dot"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"]["mode"] == "dot"

        # Switch to proxy mode
        mock_set_mode.return_value = {
            "success": True,
            "message": "Mode changed to proxy",
            "status": {"connected": True, "mode": "proxy"}
        }

        response = client.post("/api/v1/warp/mode", json={"mode": "proxy"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"]["mode"] == "proxy"


class TestWARPErrorHandling:
    """Test WARP endpoint error handling."""

    @patch(WARP_GET_STATUS_PATH)
    def test_warp_service_unavailable(self, mock_get_status, client):
        """Test handling when WARP service is unavailable."""
        mock_get_status.side_effect = Exception("WARP service unavailable")

        response = client.get("/api/v1/warp/status")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch(WARP_CONNECT_PATH)
    def test_warp_connection_timeout(self, mock_connect, client):
        """Test handling WARP connection timeout."""
        mock_connect.side_effect = TimeoutError("Connection timeout")

        response = client.post("/api/v1/warp/connect")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch(WARP_SET_MODE_PATH)
    def test_warp_mode_change_error(self, mock_set_mode, client):
        """Test handling WARP mode change errors."""
        mock_set_mode.side_effect = Exception("Failed to change mode")

        request_data = {"mode": "warp"}
        response = client.post("/api/v1/warp/mode", json=request_data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

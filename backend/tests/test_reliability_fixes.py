"""
Regression tests for the reliability hardening:
- #128: warp-cli modern subcommands with legacy fallback
- #129: configurable engine status timeouts with a single retry
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.services.warp_service import WarpService


class TestWarpCliFallback:
    """WarpService must speak modern warp-cli and fall back to legacy."""

    def _make_service(self, responses):
        """Build a WarpService whose _run_command replays canned responses
        keyed by the joined argument string, recording every call."""
        service = WarpService()
        calls = []

        async def fake_run(args):
            calls.append(list(args))
            key = " ".join(args)
            return responses.get(key, (1, "", f"error: unrecognized subcommand '{args[0]}'"))

        service._run_command = fake_run
        return service, calls

    def test_status_uses_registration_show_on_modern_cli(self):
        responses = {
            "status": (0, "Status update: Connected", ""),
            "settings": (0, "Mode: Warp", ""),
            "registration show": (0, "Account type: Team\nDevice ID: abc", ""),
            "tunnel stats": (0, "WAN IP: 104.28.1.2", ""),
        }
        service, calls = self._make_service(responses)
        status = asyncio.run(service.get_status())

        assert status["connected"] is True
        assert status["account_type"] == "team"
        assert status["ip"] == "104.28.1.2"
        assert ["registration", "show"] in calls
        assert ["account"] not in calls

    def test_status_falls_back_to_legacy_subcommands(self):
        responses = {
            "status": (0, "Status update: Connected", ""),
            "settings": (0, "Mode: Warp", ""),
            "registration show": (1, "", "error: unrecognized subcommand 'registration'"),
            "account": (0, "Type: Premium", ""),
            "tunnel stats": (1, "", "error: unrecognized subcommand 'tunnel'"),
            "warp-stats": (0, "WAN IP: 104.28.9.9", ""),
        }
        service, calls = self._make_service(responses)
        status = asyncio.run(service.get_status())

        assert status["account_type"] == "premium"
        assert status["ip"] == "104.28.9.9"
        assert ["account"] in calls
        assert ["warp-stats"] in calls

    def test_non_subcommand_errors_do_not_trigger_fallback(self):
        """A modern subcommand failing for another reason must not run the
        legacy spelling (which modern clients reject noisily)."""
        responses = {
            "status": (0, "Status update: Connected", ""),
            "settings": (0, "Mode: Warp", ""),
            "registration show": (1, "", "Registration Missing"),
            "tunnel stats": (1, "", "Unable to connect to the daemon"),
        }
        service, calls = self._make_service(responses)
        status = asyncio.run(service.get_status())

        assert status["account_type"] == "free"
        assert ["account"] not in calls
        assert ["warp-stats"] not in calls


class TestChannelStatusTimeouts:
    """ChannelStatusService retries a timed-out engine probe before marking
    a channel offline, with a configurable timeout."""

    def _make_service(self, db_session):
        from app.services.channel_status_service import ChannelStatusService

        service = ChannelStatusService(db_session)
        service.settings_repo.set_setting(service.settings_repo.ACE_ENGINE_URL, "http://engine:6878")
        return service

    def _make_channel(self, db_session):
        import uuid
        from app.models.models import AcestreamChannel

        channel = AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Timeout Test Channel",
            source_url="acestream://timeouttest",
            is_active=True,
        )
        db_session.add(channel)
        db_session.commit()
        return channel

    def test_timeout_setting_is_read(self, db_session):
        service = self._make_service(db_session)
        assert service._get_timeout() == 10.0
        service.settings_repo.set_setting(
            service.settings_repo.ACESTREAM_CHECK_TIMEOUT, "25"
        )
        assert service._get_timeout() == 25.0

    def test_invalid_timeout_setting_falls_back(self, db_session):
        service = self._make_service(db_session)
        service.settings_repo.set_setting(
            service.settings_repo.ACESTREAM_CHECK_TIMEOUT, "not-a-number"
        )
        assert service._get_timeout() == 10.0
        service.settings_repo.set_setting(
            service.settings_repo.ACESTREAM_CHECK_TIMEOUT, "-3"
        )
        assert service._get_timeout() == 10.0

    def test_slow_engine_gets_one_retry_before_offline(self, db_session):
        service = self._make_service(db_session)
        channel = self._make_channel(db_session)

        attempts = []

        async def fake_fetch(status_url, params, timeout):
            attempts.append(timeout)
            if len(attempts) == 1:
                raise asyncio.TimeoutError()
            return 200, {"response": {"is_live": 1}, "error": None}, None

        service._fetch_engine_response = fake_fetch
        result = asyncio.run(service.check_channel_status(channel))

        assert result["is_online"] is True
        assert len(attempts) == 2
        # Retry uses a doubled timeout
        assert attempts[1] == attempts[0] * 2

    def test_double_timeout_marks_offline(self, db_session):
        service = self._make_service(db_session)
        channel = self._make_channel(db_session)

        async def always_timeout(status_url, params, timeout):
            raise asyncio.TimeoutError()

        service._fetch_engine_response = always_timeout
        result = asyncio.run(service.check_channel_status(channel))

        assert result["is_online"] is False
        assert result["error"] == "Request timeout"


class TestAcestreamStatusProbeRetry:
    """AcestreamStatusService retries a timed-out probe once."""

    def test_probe_retries_on_timeout(self):
        import requests as requests_module
        from app.services.acestream_status_service import AcestreamStatusService

        service = AcestreamStatusService(engine_url="http://engine:6878")
        ok = MagicMock(status_code=200)

        with patch(
            "app.services.acestream_status_service.requests.get",
            side_effect=[requests_module.exceptions.Timeout(), ok],
        ) as mock_get:
            response = service._probe("http://engine:6878/x", 10)

        assert response is ok
        assert mock_get.call_count == 2
        assert mock_get.call_args_list[1].kwargs["timeout"] == 20

    def test_timeout_env_is_read(self, monkeypatch):
        from app.services.acestream_status_service import AcestreamStatusService

        service = AcestreamStatusService(engine_url="http://engine:6878")
        monkeypatch.setenv("ACESTREAM_STATUS_TIMEOUT", "7.5")
        assert service._get_timeout() == 7.5
        monkeypatch.setenv("ACESTREAM_STATUS_TIMEOUT", "garbage")
        assert service._get_timeout() == 10.0

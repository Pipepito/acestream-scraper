"""A host without warp-cli must not spam ERROR logs on every status poll."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch
import pytest

from app.services.warp_service import WarpService


def test_missing_warp_cli_is_reported_once_as_warning():
    WarpService._missing_binary_logged = False
    service = WarpService()
    service.logger = MagicMock()

    with patch("app.services.warp_service.subprocess.Popen", side_effect=FileNotFoundError(2, "No such file", "warp-cli")):
        first = asyncio.run(service._run_command(["status"]))
        second = asyncio.run(service._run_command(["status"]))

    assert first[0] == 127 and "not installed" in first[2]
    assert second[0] == 127
    assert service.logger.warning.call_count == 1
    assert service.logger.debug.call_count >= 1
    service.logger.error.assert_not_called()


@pytest.mark.parametrize("enabled,args,error,expected_error", [
    ("false", ["status"], "Unable to connect to the CloudflareWARP daemon: No such file", False),
    ("0", ["status"], "Unable to connect to the CloudflareWARP daemon: No such file", False),
    ("true", ["status"], "Unable to connect to the CloudflareWARP daemon: No such file", True),
    ("", ["status"], "Unable to connect to the CloudflareWARP daemon: No such file", True),
    ("false", ["connect"], "Unable to connect to the CloudflareWARP daemon: No such file", True),
    ("false", ["status"], "Permission denied", True),
])
def test_disabled_daemon_status_is_expected_but_other_failures_stay_visible(
    monkeypatch, enabled, args, error, expected_error,
):
    monkeypatch.setenv("ENABLE_WARP", enabled)
    service = WarpService()
    service.logger = MagicMock()
    process = MagicMock(returncode=1)
    process.communicate.return_value = ("", error)
    with patch("app.services.warp_service.subprocess.Popen", return_value=process):
        result = asyncio.run(service._run_command(args))
    assert result == (1, "", error)
    assert service.logger.error.called is expected_error

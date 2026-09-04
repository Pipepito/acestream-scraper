"""A host without warp-cli must not spam ERROR logs on every status poll."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

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

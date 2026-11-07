"""The pinned image probe supports both legacy and first-run-account images."""
import importlib.util
import io
import json
from pathlib import Path
import urllib.error
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("image_acceptance", ROOT / "docker/testdata/image_acceptance.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def http_error(code):
    return urllib.error.HTTPError("http://127.0.0.1:8000/api/v1/auth/status", code, "fixture", {}, None)


def test_legacy_image_without_accounts_keeps_existing_runtime_checks():
    with patch.object(probe.urllib.request, "build_opener") as factory:
        factory.return_value.open.side_effect = http_error(404)
        probe.first_run_accounts()
        assert factory.return_value.open.call_count == 1


@pytest.mark.parametrize("code", [401, 403, 500, 503])
def test_account_status_errors_cannot_be_mistaken_for_legacy_images(code):
    with patch.object(probe.urllib.request, "build_opener") as factory:
        factory.return_value.open.side_effect = http_error(code)
        with pytest.raises(urllib.error.HTTPError) as error:
            probe.first_run_accounts()
        assert error.value.code == code


def test_pending_accounts_require_locked_routes_and_explicit_bootstrap():
    response = io.BytesIO(b"{}")
    response.status = 200
    with patch.object(probe.urllib.request, "build_opener") as factory, patch.object(probe, "fetch") as fetch:
        factory.return_value.open.side_effect = [io.BytesIO(b'{"mode":"pending","csrf":"test-csrf"}'), response]
        fetch.side_effect = http_error(401)
        probe.first_run_accounts()
        assert [call.args[0] for call in fetch.call_args_list] == [
            "http://127.0.0.1:8000/api/v1/config", "http://127.0.0.1:8000/openapi.json"]
        request = factory.return_value.open.call_args.args[0]
        assert request.full_url.endswith("/api/v1/auth/bootstrap")
        assert request.get_header("X-csrf-token") == "test-csrf"
        assert json.loads(request.data)["enabled"] is False


def test_pending_accounts_with_public_configuration_fail_acceptance():
    with patch.object(probe.urllib.request, "build_opener") as factory, patch.object(probe, "fetch", return_value=b"{}"):
        factory.return_value.open.return_value = io.BytesIO(b'{"mode":"pending","csrf":"test-csrf"}')
        with pytest.raises(AssertionError, match="Pending setup exposed"):
            probe.first_run_accounts()
        assert factory.return_value.open.call_count == 1

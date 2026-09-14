import importlib.util
from pathlib import Path
from urllib.error import HTTPError

import pytest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("hub_description", ROOT / "scripts/ci/publish_dockerhub_description.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)
PAYLOAD = {"description": "Project summary", "full_description": "# Project\n"}


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setenv("DOCKERHUB_USERNAME", "test-user")
    monkeypatch.setenv("DOCKERHUB_TOKEN", "test-secret")


def test_update_only_description_fields_and_verify(monkeypatch, credentials):
    calls = []
    responses = iter([{"access_token": "test-bearer"}, {}, {}, PAYLOAD])

    def request(method, path, payload=None, token=None):
        calls.append((method, path, payload, token))
        return next(responses)

    monkeypatch.setattr(hub, "request", request)
    hub.publish(PAYLOAD)
    assert calls == [
        ("POST", "/v2/auth/token", {"identifier": "test-user", "secret": "test-secret"}, None),
        ("GET", "/v2/repositories/pipepito/acestream-scraper/", None, "test-bearer"),
        ("PATCH", "/v2/repositories/pipepito/acestream-scraper/", PAYLOAD, "test-bearer"),
        ("GET", "/v2/repositories/pipepito/acestream-scraper/", None, "test-bearer"),
    ]


def test_matching_description_is_not_written(monkeypatch, credentials):
    methods = []

    def request(method, *args, **kwargs):
        methods.append(method)
        return {"access_token": "token"} if method == "POST" else PAYLOAD

    monkeypatch.setattr(hub, "request", request)
    hub.publish(PAYLOAD)
    assert methods == ["POST", "GET"]


def test_failed_verification_is_not_reported_as_success(monkeypatch, credentials):
    responses = iter([{"access_token": "token"}, {}, {}, {}])
    monkeypatch.setattr(hub, "request", lambda *a, **kw: next(responses))
    with pytest.raises(RuntimeError, match="verification failed"):
        hub.publish(PAYLOAD)


def test_dry_run_needs_no_credentials_or_network(monkeypatch, capsys):
    monkeypatch.delenv("DOCKERHUB_USERNAME", raising=False)
    monkeypatch.delenv("DOCKERHUB_TOKEN", raising=False)
    monkeypatch.setattr("sys.argv", ["publisher", "--dry-run"])
    monkeypatch.setattr(hub, "request", lambda *a, **kw: pytest.fail("dry run called network"))
    hub.main()
    assert '"full_description"' in capsys.readouterr().out


def test_http_error_does_not_expose_server_body_or_credentials(monkeypatch):
    class Opener:
        def open(self, *args, **kwargs):
            raise HTTPError("https://hub.docker.com", 403, "secret echoed in message", {}, None)

    monkeypatch.setattr(hub, "build_opener", lambda *a: Opener())
    with pytest.raises(RuntimeError) as exc:
        hub.request("PATCH", "/test", PAYLOAD, "secret")
    assert str(exc.value) == "Docker Hub PATCH failed (HTTP 403)"


def test_redirects_are_refused():
    assert hub.NoRedirects().redirect_request(None, None, 302, "", {}, "https://example.invalid") is None

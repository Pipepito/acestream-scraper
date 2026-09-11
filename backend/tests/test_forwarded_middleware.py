"""ForwardedHeadersMiddleware: the app, not uvicorn, decides which peers'
X-Forwarded-* headers to trust (spec 4.3)."""
import pytest
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

import main
from app.config.settings import get_settings
from app.middleware.forwarded import ForwardedHeadersMiddleware, parse_trusted


def _probe_app() -> FastAPI:
    app = FastAPI()

    @app.get("/probe")
    async def probe(request: Request):
        return {
            "scheme": request.url.scheme,
            "host": request.url.netloc,
            "client": request.client.host if request.client else None,
            "peer": list(request.state.peer),
            "forwarded": request.state.forwarded,
        }

    return app


def _app(trusted: str) -> TestClient:
    app = _probe_app()
    app.add_middleware(ForwardedHeadersMiddleware, trusted=parse_trusted(trusted))
    return TestClient(app)


FORWARDED = {
    "X-Forwarded-Proto": "https",
    "X-Forwarded-Host": "scraper.example.com",
    "X-Forwarded-For": "203.0.113.7",
}


def test_trusted_peer_headers_rewrite_scheme_host_and_client():
    body = _app("testclient").get("/probe", headers=FORWARDED).json()
    assert body["scheme"] == "https"
    assert body["host"] == "scraper.example.com"
    assert body["client"] == "203.0.113.7"
    assert body["peer"] == ["testclient", 50000]
    assert body["forwarded"] is True


def test_untrusted_peer_headers_are_ignored():
    body = _app("10.0.0.0/8").get("/probe", headers=FORWARDED).json()
    assert body["scheme"] == "http"
    assert body["host"] == "testserver"
    assert body["client"] == "testclient"
    assert body["forwarded"] is False


def test_rightmost_untrusted_hop_wins_and_all_trusted_keeps_raw_peer():
    client = _app("testclient,10.0.0.0/8")
    body = client.get("/probe", headers={"X-Forwarded-For": "198.51.100.9, 10.1.1.1"}).json()
    assert body["client"] == "198.51.100.9"
    body = client.get("/probe", headers={"X-Forwarded-For": "10.1.1.1, 10.2.2.2"}).json()
    assert body["client"] == "testclient"


def test_invalid_proto_is_ignored():
    body = _app("testclient").get("/probe", headers={"X-Forwarded-Proto": "gopher"}).json()
    assert body["scheme"] == "http"


def test_wildcard_trusts_everyone():
    body = _app("*").get("/probe", headers=FORWARDED).json()
    assert body["forwarded"] is True


@pytest.mark.parametrize(
    ("spec", "host", "expected"),
    [
        ("127.0.0.1", "127.0.0.1", True),
        ("10.0.0.0/8", "10.20.30.40", True),
        ("10.0.0.0/8", "192.168.1.1", False),
        ("testclient", "testclient", True),
        ("::1/128", "::1", True),
        ("192.168.0.0/16", "::ffff:192.168.1.5", True),
        ("bogus/99, 10.0.0.0/8", "10.0.0.1", True),
        ("", "10.0.0.1", False),
    ],
)
def test_parse_trusted(spec, host, expected):
    assert parse_trusted(spec).contains(host) is expected


def test_repeated_forwarded_for_headers_cannot_be_forged_by_the_client():
    """A proxy that appends a second X-Forwarded-For line must still win.

    The client sends its own line ("100.64.0.1" — inside TUNER_ALLOWED_NETWORKS
    but not FORWARDED_ALLOW_IPS) and the proxy appends the real peer as a
    separate header. Both lines are one field value, so the right-most
    untrusted hop is the real client, not the forged entry.
    """
    body = _app("testclient,10.0.0.0/8").get(
        "/probe",
        headers=[
            ("X-Forwarded-For", "100.64.0.1"),
            ("X-Forwarded-For", "203.0.113.7, 10.1.1.1"),
        ],
    ).json()
    assert body["client"] == "203.0.113.7"


def test_main_registers_the_middleware_as_the_outermost_user_middleware():
    """main.py must keep the registration, after the CORS add_middleware call.

    add_middleware inserts at the head of user_middleware, so the outermost
    layer is the last one registered: index 0 must be this middleware (spec
    4.3 — it runs before CORS, the correlation-id middleware, auth and the
    tuner allowlist).
    """
    registered = [middleware.cls for middleware in main.app.user_middleware]
    assert registered[0] is ForwardedHeadersMiddleware, registered
    assert CORSMiddleware in registered[1:], registered
    assert main.app.user_middleware[0].kwargs["trusted"] == parse_trusted(
        get_settings().FORWARDED_ALLOW_IPS
    )


def test_main_middleware_stack_corrects_the_request_for_a_trusted_proxy_peer():
    """Drive a request through main.app's registered middleware, unmodified.

    Rebuilding the stack around a probe endpoint proves the kwargs main.py
    passes actually rewrite the request for a peer inside the default
    FORWARDED_ALLOW_IPS (10.0.0.0/8) and record the raw peer.
    """
    stack = _probe_app()
    for middleware in reversed(main.app.user_middleware):
        stack = middleware.cls(stack, *middleware.args, **middleware.kwargs)

    body = TestClient(stack, client=("10.1.2.3", 4321)).get("/probe", headers=FORWARDED).json()
    assert body["scheme"] == "https"
    assert body["host"] == "scraper.example.com"
    assert body["client"] == "203.0.113.7"
    assert body["peer"] == ["10.1.2.3", 4321]
    assert body["forwarded"] is True

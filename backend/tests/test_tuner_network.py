"""Token-free /tuner/* routes are gated by TUNER_ALLOWED_NETWORKS on both the
raw peer and the forwarded client (spec 4.4)."""
import httpx
import pytest

from app.config.settings import get_settings
from app.services.tuner_network import TunerNetworkGate, get_tuner_gate

IH = "0" * 40


@pytest.fixture
def gate_env(monkeypatch):
    def apply(spec: str):
        monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", spec)
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()
    yield apply
    get_settings.cache_clear()
    get_tuner_gate.cache_clear()


@pytest.mark.parametrize(("spec", "host", "expected"), [
    ("192.168.0.0/16", "192.168.1.5", True),
    ("192.168.0.0/16", "::ffff:192.168.1.5", True),
    ("192.168.0.0/16", "203.0.113.4", False),
    ("*", "203.0.113.4", True),
    ("", "127.0.0.1", False),
    ("testclient", "testclient", True),
])
def test_gate_membership(spec, host, expected):
    assert TunerNetworkGate(spec).is_allowed(host) is expected


def test_default_allows_tailscale_and_link_local_but_not_public():
    gate = TunerNetworkGate(get_settings().TUNER_ALLOWED_NETWORKS)
    assert gate.is_allowed("100.64.0.1")
    assert gate.is_allowed("fe80::1")
    assert not gate.is_allowed("8.8.8.8")


def test_classify_source():
    gate = TunerNetworkGate("*")
    assert gate.classify_source("127.0.0.1", False) == "loopback"
    assert gate.classify_source("172.17.0.1", False) == "docker-gateway"
    assert gate.classify_source("192.168.65.1", False) == "docker-gateway"
    assert gate.classify_source("192.168.1.9", False) == "direct"
    assert gate.classify_source("172.17.0.1", True) == "forwarded"


def test_denials_ring_buffer():
    gate = TunerNetworkGate("10.0.0.0/8")
    for i in range(25):
        gate.record_denial(f"203.0.113.{i}", f"203.0.113.{i}", "/tuner/lineup.json")
    denials = gate.recent_denials()
    assert len(denials) == 20
    assert denials[0].client_ip == "203.0.113.24"


def test_stream_route_denied_outside_allowlist(client, gate_env):
    gate_env("10.0.0.0/8")
    response = client.get(f"/tuner/stream/{IH}.ts")
    assert response.status_code == 403
    body = response.json()["error"]
    assert body["code"] == "TUNER_NETWORK_DENIED"
    assert body["context"]["client_ip"] == "testclient"
    assert body["context"]["allowed_networks"] == ["10.0.0.0/8"]
    assert get_tuner_gate().recent_denials()[0].path == f"/tuner/stream/{IH}.ts"


def test_spoofed_forwarded_for_cannot_pass_a_narrow_allowlist(client, gate_env, monkeypatch):
    # Peer "testclient" is trusted for forwarding but not in the tuner allowlist.
    gate_env("192.168.1.20/32")
    import main
    from app.middleware.forwarded import ForwardedHeadersMiddleware, parse_trusted
    for layer in main.app.user_middleware:
        if layer.cls is ForwardedHeadersMiddleware:
            layer.kwargs["trusted"] = parse_trusted("testclient")
    main.app.middleware_stack = None
    try:
        response = client.get(f"/tuner/stream/{IH}.ts", headers={"X-Forwarded-For": "192.168.1.20"})
        assert response.status_code == 403
    finally:
        for layer in main.app.user_middleware:
            if layer.cls is ForwardedHeadersMiddleware:
                layer.kwargs["trusted"] = parse_trusted(get_settings().FORWARDED_ALLOW_IPS)
        main.app.middleware_stack = None


def test_unknown_tuner_path_is_json_404_not_spa(client, gate_env):
    gate_env("*")
    response = client.get("/tuner/does-not-exist.json")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Unknown tuner path"}


def test_head_stream_answers_headers_without_engine(client, gate_env, monkeypatch):
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    monkeypatch.setattr(tuner_module, "_engine", lambda db: (_ for _ in ()).throw(AssertionError("engine must not be called on HEAD")))
    response = client.head(f"/tuner/stream/{IH}.ts")
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp2t"
    assert response.headers["cache-control"] == "no-store"


def test_stream_route_relays_bytes_and_ignores_transcode_param(client, gate_env, monkeypatch):
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    from app.services.engine_client import EngineClient
    body = b"\x47" * 188 * 10

    def handler(request):
        p = request.url.path
        if p == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        if p.startswith("/content/"):
            return httpx.Response(200, content=body, headers={"Content-Type": "video/mp2t"})
        return httpx.Response(200, text="ok")

    monkeypatch.setattr(tuner_module, "_engine", lambda db: EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler))))
    monkeypatch.setattr(tuner_module, "_relay_client_factory", lambda **kw: httpx.AsyncClient(transport=httpx.MockTransport(handler), **kw))
    response = client.get(f"/tuner/stream/{IH}.ts?transcode=heavy")
    assert response.status_code == 200
    assert response.content == body


def test_stream_route_maps_engine_refusal_to_502(client, gate_env, monkeypatch):
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    from app.services.engine_client import EngineClient

    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "activate premium"})

    monkeypatch.setattr(tuner_module, "_engine", lambda db: EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler))))
    response = client.get(f"/tuner/stream/{IH}.ts")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ENGINE_REFUSED"


def test_unconfigured_engine_url_is_502_not_500(client, gate_env, monkeypatch):
    """A missing/blank ace_engine_url raises before the relay starts; it is an
    upstream failure, so it answers 502 like every other engine error."""
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    from app.services.engine_client import EngineUnavailableError

    def unconfigured(db):
        raise EngineUnavailableError("Acestream Engine URL is not configured")

    monkeypatch.setattr(tuner_module, "_engine", unconfigured)
    response = client.get(f"/tuner/stream/{IH}.ts")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ENGINE_UNAVAILABLE"


def test_stream_route_releases_the_engine_client(client, gate_env, monkeypatch):
    """The per-request EngineClient owns an httpx connection pool: the route
    closes it on the streamed path and on the early-failure path."""
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    from app.services.engine_client import EngineClient

    closed = []
    started = httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
    refused = httpx.Response(200, json={"response": None, "error": "activate premium"})

    def build(getstream_response):
        def handler(request):
            if request.url.path == "/ace/getstream":
                return httpx.Response(getstream_response.status_code, content=getstream_response.content, headers={"Content-Type": "application/json"})
            if request.url.path.startswith("/content/"):
                return httpx.Response(200, content=b"\x47" * 188, headers={"Content-Type": "video/mp2t"})
            return httpx.Response(200, text="ok")

        engine = EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler)))
        inner_close = engine.close

        def tracking_close():
            closed.append(engine.engine_url)
            inner_close()

        engine.close = tracking_close
        return engine, handler

    for reply, expected_status in ((started, 200), (refused, 502)):
        engine, handler = build(reply)
        monkeypatch.setattr(tuner_module, "_engine", lambda db, engine=engine: engine)
        monkeypatch.setattr(tuner_module, "_relay_client_factory", lambda handler=handler, **kw: httpx.AsyncClient(transport=httpx.MockTransport(handler), **kw))
        assert client.get(f"/tuner/stream/{IH}.ts").status_code == expected_status

    assert len(closed) == 2


def test_invalid_content_id_is_422(client, gate_env):
    gate_env("*")
    assert client.get("/tuner/stream/not-hex.ts").status_code == 422

"""Byte relay from the engine (spec 4.2)."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError
from app.services.stream_relay import (
    RELAY_HEADERS, ClosingStreamingResponse, EngineStreamError, RelayRegistry, relay_engine_stream,
)

IH = "0" * 40
BODY = b"\x47" * 188 * 50


def _fake_engine(calls, *, redirect_host="engine", content_status=200):
    """MockTransport handler: JSON start -> 302 -> bytes; records stop calls."""
    def handler(request):
        calls.append((request.method, str(request.url)))
        path = request.url.path
        if path == "/ace/getstream":
            return httpx.Response(200, json={"response": {
                "playback_url": f"http://engine:6878/ace/r/{IH}/tok",
                "stat_url": f"http://engine:6878/ace/stat/{IH}/s",
                "command_url": f"http://engine:6878/ace/cmd/{IH}/s", "is_live": 1}, "error": None})
        if path.startswith("/ace/r/"):
            return httpx.Response(302, headers={"Location": f"http://{redirect_host}:6878/content/{IH}/1"})
        if path.startswith("/content/"):
            return httpx.Response(content_status, content=BODY if content_status == 200 else b"", headers={"Content-Type": "video/mp2t"})
        if path.startswith("/ace/cmd/"):
            return httpx.Response(200, text="ok")
        return httpx.Response(404)
    return handler


def _engine_and_factory(handler):
    sync_client = httpx.Client(transport=httpx.MockTransport(handler))
    engine = EngineClient("http://engine:6878", client=sync_client)

    def factory(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), **kwargs)
    return engine, factory


def _collect(gen):
    async def run():
        chunks = []
        async for chunk in gen:
            chunks.append(chunk)
        return b"".join(chunks)
    return asyncio.run(run())


def test_relay_follows_engine_redirect_and_stops_once():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls))
    body = _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))
    assert body == BODY
    stops = [u for m, u in calls if "/ace/cmd/" in u]
    assert stops == [f"http://engine:6878/ace/cmd/{IH}/s?method=stop"]


def test_redirect_to_another_host_is_refused():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls, redirect_host="evil"))
    with pytest.raises(EngineStreamError):
        _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))
    assert sum("/ace/cmd/" in u for _, u in calls) == 1


def test_non_200_upstream_is_refused_with_one_stop():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls, content_status=500))
    with pytest.raises(EngineStreamError):
        _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))
    assert sum("/ace/cmd/" in u for _, u in calls) == 1


def test_engine_refusal_propagates_before_any_bytes():
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "activate premium"})
    engine, factory = _engine_and_factory(handler)
    with pytest.raises(EngineRefusedError):
        _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))


def test_unreachable_engine_propagates_before_any_bytes():
    calls = []

    def handler(request):
        calls.append((request.method, str(request.url)))
        raise httpx.ConnectError("no route to engine", request=request)

    engine, factory = _engine_and_factory(handler)
    with pytest.raises(EngineUnavailableError):
        _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))
    assert [u for _, u in calls if "/ace/cmd/" in u] == []


def test_relay_registers_itself_and_releases_on_close():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls))
    registry = RelayRegistry()

    async def run():
        gen = relay_engine_stream(engine, IH, "vlc", client_factory=factory, registry=registry)
        await gen.__anext__()
        active = registry.active()
        await gen.aclose()
        return active

    active = asyncio.run(run())
    assert [(info.content_id, info.client_label) for info in active] == [(IH, "vlc")]
    assert active[0].bytes_sent == len(BODY)
    assert registry.count_active() == 0


def test_cancelled_consumer_stops_engine_session_exactly_once():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls))

    async def run():
        gen = relay_engine_stream(engine, IH, "test", client_factory=factory)
        await gen.__anext__()
        await gen.aclose()
    asyncio.run(run())
    assert sum("/ace/cmd/" in u for _, u in calls) == 1


def _http_scope():
    """A scope shaped like uvicorn's (spec_version 2.3 -> Starlette watches for
    ``http.disconnect`` rather than waiting for ``send`` to raise)."""
    return {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/s", "raw_path": b"/s", "query_string": b"", "root_path": "",
        "headers": [], "client": ("127.0.0.1", 5000), "server": ("testserver", 80),
    }


def _endless_body(closed):
    """A body that only ever suspends at ``yield``: it awaits nothing itself, so
    its ``finally`` can only run via ``aclose()`` -- never by a cancellation
    landing inside its own frame. That is what makes the tests below
    discriminating."""
    async def body():
        try:
            while True:
                yield b"x" * 1024
        finally:
            closed.set()
    return body()


def _blocking_send(sent, streaming):
    """Records ASGI messages and parks inside ``send`` after the first body
    chunk, so the client goes away while the body generator sits at its yield."""
    async def send(message):
        sent.append(message)
        if message["type"] == "http.response.body":
            streaming.set()
            await asyncio.sleep(0.05)
        else:
            await asyncio.sleep(0)
    return send


def test_closing_streaming_response_closes_generator_on_client_disconnect():
    """The client vanishes mid-stream: Starlette cancels the send loop and drops
    the body iterator, so the relay's ``finally`` (which stops the engine
    session) only runs because this subclass closes it.

    Driven through the raw ASGI interface on purpose: ``TestClient`` runs the
    app to completion and buffers the body before handing back a response, and
    its ``receive`` reports ``http.disconnect`` only once the response is
    already complete, so it cannot express a mid-stream disconnect at all.
    """
    closed = asyncio.Event()
    streaming = asyncio.Event()
    sent = []

    async def receive():
        await streaming.wait()
        return {"type": "http.disconnect"}

    async def run():
        response = ClosingStreamingResponse(_endless_body(closed), headers=RELAY_HEADERS)
        await asyncio.wait_for(response(_http_scope(), receive, _blocking_send(sent, streaming)), timeout=5)
        # Asserted inside the loop: asyncio.run() finalises stray async
        # generators on the way out, which would hide a missing aclose().
        return closed.is_set()

    assert asyncio.run(run()) is True
    headers = dict(sent[0]["headers"])
    assert sent[0]["type"] == "http.response.start"
    assert headers[b"content-type"] == b"video/mp2t"
    assert headers[b"cache-control"] == b"no-store"
    assert headers[b"x-accel-buffering"] == b"no"


def test_closing_streaming_response_closes_generator_when_cancelled():
    """Uvicorn cancels in-flight relay tasks on graceful shutdown; the shielded
    aclose() still has to run the generator's cleanup."""
    closed = asyncio.Event()
    streaming = asyncio.Event()
    sent = []

    async def receive():
        await asyncio.Event().wait()  # no disconnect; the task is cancelled instead
        raise AssertionError("unreachable")

    async def run():
        response = ClosingStreamingResponse(_endless_body(closed), headers=RELAY_HEADERS)
        task = asyncio.create_task(response(_http_scope(), receive, _blocking_send(sent, streaming)))
        await asyncio.wait_for(streaming.wait(), timeout=5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=5)
        return closed.is_set()

    assert asyncio.run(run()) is True


def test_relay_headers_reach_the_client_through_a_route():
    payload = b"\x47" * 188

    async def body():
        yield payload

    app = FastAPI()

    @app.get("/s")
    async def stream():
        return ClosingStreamingResponse(body(), headers=RELAY_HEADERS)

    with TestClient(app) as client:
        response = client.get("/s")
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp2t"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-accel-buffering"] == "no"
    assert response.content == payload


def test_registry_tracks_and_reaps():
    registry = RelayRegistry()
    info = registry.open("c" * 40, "vlc")
    assert registry.count_active() == 1
    registry.close(info.id)
    assert registry.count_active() == 0
    assert registry.reap_finished(older_than_seconds=0) == 1
    assert registry.active() == []

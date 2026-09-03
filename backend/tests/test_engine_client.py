import json

import httpx
import pytest

from app.services.engine_client import (
    EngineClient, EngineRefusedError, EngineSession, EngineUnavailableError, engine_url_from_settings,
)

IH = "00c505e3e33687ecac47ef2a555497e66ebdc5af"
CID = "a" * 40


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://engine:6878")


def test_start_parses_the_json_contract():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"response": {
            "playback_url": "http://engine:6878/ace/r/%s/tok" % IH,
            "stat_url": "http://engine:6878/ace/stat/%s/s1" % IH,
            "command_url": "http://engine:6878/ace/cmd/%s/s1" % IH,
            "is_live": 1, "playback_session_id": "s1"}, "error": None})

    session = EngineClient("http://engine:6878", client=_client(handler)).start(CID, pid="p1")
    assert seen["url"] == f"http://engine:6878/ace/getstream?id={CID}&pid=p1&format=json"
    assert session == EngineSession(content_id=CID, pid="p1", playback_url=f"http://engine:6878/ace/r/{IH}/tok",
                                    stat_url=f"http://engine:6878/ace/stat/{IH}/s1",
                                    command_url=f"http://engine:6878/ace/cmd/{IH}/s1", is_live=True)


def test_start_generates_a_pid_when_absent():
    def handler(request):
        assert len(request.url.params["pid"]) == 32
        return httpx.Response(200, json={"response": {"playback_url": "u", "stat_url": "s", "command_url": "c", "is_live": 0}, "error": None})
    assert EngineClient("http://engine:6878", client=_client(handler)).start(CID).is_live is False


def test_engine_error_is_refused():
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "To continue, you need to activate premium"})
    with pytest.raises(EngineRefusedError, match="activate premium"):
        EngineClient("http://engine:6878", client=_client(handler)).start(CID)


@pytest.mark.parametrize("make", [lambda r: httpx.Response(500, text="boom"), lambda r: (_ for _ in ()).throw(httpx.ConnectError("down"))])
def test_transport_failures_are_unavailable(make):
    with pytest.raises(EngineUnavailableError):
        EngineClient("http://engine:6878", client=_client(make)).start(CID)


def test_stop_and_stat():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if "cmd" in request.url.path:
            return httpx.Response(200, text="ok")
        return httpx.Response(200, json={"response": {"status": "dl", "peers": 7, "speed_down": 1200, "speed_up": 30}, "error": None})

    client = EngineClient("http://engine:6878", client=_client(handler))
    session = EngineSession(CID, "p", "u", "http://engine:6878/ace/stat/x/s", "http://engine:6878/ace/cmd/x/s", True)
    stats = client.stat(session)
    assert (stats.status, stats.peers, stats.speed_down, stats.speed_up) == ("dl", 7, 1200, 30)
    client.stop(session)  # errors are swallowed; the call must happen
    assert calls[-1] == "http://engine:6878/ace/cmd/x/s?method=stop"


def test_stop_swallows_errors():
    def handler(request):
        raise httpx.ConnectError("gone")
    EngineClient("http://engine:6878", client=_client(handler)).stop(EngineSession(CID, "p", "u", "s", "http://engine:6878/ace/cmd/x/s", True))


def test_engine_url_from_settings_normalizes(db_session):
    from app.repositories.settings_repository import SettingsRepository
    repo = SettingsRepository(db_session)
    repo.set_setting("ace_engine_url", "engine.lan:6878/")
    assert engine_url_from_settings(repo) == "http://engine.lan:6878"


def test_close_releases_a_client_it_created():
    client = EngineClient("http://engine:6878")
    pool = client._client
    client.close()
    assert pool.is_closed is True


def test_context_manager_closes_a_client_it_created():
    with EngineClient("http://engine:6878") as client:
        pool = client._client
        assert pool.is_closed is False
    assert pool.is_closed is True


def test_an_injected_client_outlives_the_engine_client():
    injected = _client(lambda request: httpx.Response(200, json={"response": {"status": "dl", "peers": 0, "speed_down": 0, "speed_up": 0}, "error": None}))
    session = EngineSession(CID, "p", "u", "http://engine:6878/ace/stat/x/s", "http://engine:6878/ace/cmd/x/s", True)
    with EngineClient("http://engine:6878", client=injected) as client:
        assert client.stat(session).status == "dl"
    assert injected.is_closed is False
    # Still usable by its owner after the EngineClient is done with it.
    assert EngineClient("http://engine:6878", client=injected).stat(session).status == "dl"
    injected.close()

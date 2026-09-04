"""VLC HTTP interface and Kodi JSON-RPC drivers (spec 6.2)."""
import json

import httpx
import pytest

from app.services.remote_players.base import (
    PlayerAuthError,
    PlayerCommandError,
    PlayerUnreachable,
    make_driver,
)
from app.services.remote_players.kodi import KodiDriver
from app.services.remote_players.vlc import VlcDriver

STATUS = {"apiversion": 3, "version": "3.0.23", "state": "playing", "time": 61, "length": 0, "volume": 256,
          "information": {"category": {"meta": {"title": "Arena TV", "filename": "stream.ts"}}}}


def _vlc(handler):
    return VlcDriver("192.168.1.20", 8080, "pw", client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_vlc_status_and_volume_scale():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=STATUS, headers={"Content-Type": "application/json"})

    status = _vlc(handler).status()
    assert seen[0].url.path == "/requests/status.json"
    assert seen[0].headers["Authorization"].startswith("Basic ")  # ("", "pw")
    assert (status.state, status.title, status.position_s, status.volume_pct) == ("playing", "Arena TV", 61, 100)


def test_vlc_play_clears_playlist_then_in_play_with_encoded_url():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json=STATUS)

    _vlc(handler).play("http://scraper.lan:8000/tuner/stream/abc.ts?x=1&y=2", "Arena TV")
    assert seen[0].endswith("/requests/status.json?command=pl_empty")
    assert "command=in_play&input=http%3A%2F%2Fscraper.lan%3A8000%2Ftuner%2Fstream%2Fabc.ts%3Fx%3D1%26y%3D2" in seen[1]


@pytest.mark.parametrize(("pct", "expected"), [(0, 0), (50, 128), (100, 256), (200, 512), (250, 512)])
def test_vlc_volume_uses_raw_scale(pct, expected):
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json=STATUS)

    _vlc(handler).set_volume(pct)
    assert seen[0] == {"command": "volume", "val": str(expected)}


def test_vlc_pause_resume_stop_commands():
    seen = []

    def handler(request):
        seen.append(request.url.params["command"])
        return httpx.Response(200, json=STATUS)

    driver = _vlc(handler)
    driver.pause(); driver.resume(); driver.stop()
    assert seen == ["pl_forcepause", "pl_forceresume", "pl_stop"]


def test_vlc_auth_errors_are_distinct():
    with pytest.raises(PlayerAuthError) as no_pw:
        _vlc(lambda r: httpx.Response(403, text="no password")).status()
    assert no_pw.value.kind == "no_password"
    with pytest.raises(PlayerAuthError) as wrong:
        _vlc(lambda r: httpx.Response(401, text="unauthorized")).status()
    assert wrong.value.kind == "wrong_password"


def test_vlc_html_error_page_is_a_command_error():
    html = "<html><body><h1>Error loading status.json</h1><pre>lua: bad argument #1 to 'set' (number expected)</pre></body></html>"
    with pytest.raises(PlayerCommandError, match="number expected"):
        _vlc(lambda r: httpx.Response(200, text=html, headers={"Content-Type": "text/html"})).set_volume(50)


def test_vlc_connection_error_is_unreachable():
    def handler(request):
        raise httpx.ConnectError("refused")
    with pytest.raises(PlayerUnreachable):
        _vlc(handler).probe()


def test_vlc_probe_reports_version():
    probe = _vlc(lambda r: httpx.Response(200, json=STATUS)).probe()
    assert probe.reachable and probe.authenticated and probe.version == "3.0.23"
    probe = _vlc(lambda r: httpx.Response(403)).probe()
    assert probe.reachable and not probe.authenticated and "password" in probe.hint.lower()


def test_drivers_refuse_forbidden_hosts(monkeypatch):
    driver = VlcDriver("169.254.169.254", 8080, "pw", client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=STATUS))))
    with pytest.raises(PlayerUnreachable, match="metadata"):
        driver.status()


def _kodi(handler):
    return KodiDriver("192.168.1.30", 8080, "kodi", "pw", client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_kodi_play_and_commands():
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append((body["method"], body.get("params")))
        if body["method"] == "Player.GetActivePlayers":
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": [{"playerid": 1, "type": "video"}]})
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": "OK"})

    driver = _kodi(handler)
    driver.play("http://x/stream.ts", "Arena TV")
    driver.pause(); driver.resume(); driver.stop(); driver.set_volume(150)
    methods = [m for m, _ in calls]
    assert methods[0] == "Player.Open" and calls[0][1] == {"item": {"file": "http://x/stream.ts"}}
    assert ("Player.PlayPause", {"playerid": 1, "play": False}) in calls
    assert ("Player.PlayPause", {"playerid": 1, "play": True}) in calls
    assert ("Player.Stop", {"playerid": 1}) in calls
    assert ("Application.SetVolume", {"volume": 100}) in calls  # clamped to 100


def test_kodi_status():
    def handler(request):
        method = json.loads(request.content)["method"]
        results = {
            "Player.GetActivePlayers": [{"playerid": 1, "type": "video"}],
            "Player.GetProperties": {"time": {"hours": 0, "minutes": 1, "seconds": 5, "milliseconds": 0}, "totaltime": {"hours": 0, "minutes": 0, "seconds": 0, "milliseconds": 0}, "speed": 0},
            "Player.GetItem": {"item": {"title": "Arena TV", "file": "http://x"}},
            "Application.GetProperties": {"volume": 80, "version": {"major": 21, "minor": 1}},
        }
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": results[method]})

    status = _kodi(handler).status()
    assert (status.state, status.title, status.position_s, status.volume_pct) == ("paused", "Arena TV", 65, 80)


def test_kodi_idle_is_stopped_and_auth_maps():
    def idle(request):
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": []})
    assert _kodi(idle).status().state == "stopped"
    with pytest.raises(PlayerAuthError) as exc:
        _kodi(lambda r: httpx.Response(401)).status()
    assert exc.value.kind == "wrong_password"
    with pytest.raises(PlayerCommandError, match="not found"):
        _kodi(lambda r: httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}})).stop()


def test_make_driver_maps_kinds():
    assert isinstance(make_driver("vlc", "192.168.1.20", 8080, None, "pw"), VlcDriver)
    assert isinstance(make_driver("kodi", "192.168.1.30", 8080, "kodi", "pw"), KodiDriver)
    with pytest.raises(ValueError, match="unknown player kind"):
        make_driver("mpv", "192.168.1.40", 8080, None, None)

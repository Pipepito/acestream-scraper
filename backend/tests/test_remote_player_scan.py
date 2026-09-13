"""Network scan for VLC/Kodi web interfaces: validation, defaults, classification (spec 6.1)."""
import asyncio
import ipaddress
import time

import httpx
import pytest

from app.services.remote_players import scan
from app.services.remote_players.scan import ScanValidationError, default_scan_cidr, scan_network, validate_scan_request


@pytest.mark.parametrize(("cidr", "code"), [
    ("8.8.8.0/22", "SCAN_CIDR_NOT_PRIVATE"), ("169.254.0.0/22", "SCAN_CIDR_NOT_PRIVATE"), ("127.0.0.0/24", "SCAN_CIDR_NOT_PRIVATE"),
    ("fd00::/22", "SCAN_TOO_LARGE"), ("10.0.0.0/8", "SCAN_TOO_LARGE"),
])
def test_validate_scan_request_rejects(cidr, code):
    with pytest.raises(ScanValidationError) as exc:
        validate_scan_request(cidr, [8080])
    assert exc.value.code == code


def test_validate_scan_request_accepts_private_and_normalises():
    network, ports = validate_scan_request("192.168.1.77/24", [8080, 8080, 80])
    assert str(network) == "192.168.1.0/24" and ports == [8080, 80]
    with pytest.raises(ScanValidationError, match="ports"):
        validate_scan_request("192.168.1.0/24", [0])
    with pytest.raises(ScanValidationError, match="ports"):
        validate_scan_request("192.168.1.0/24", list(range(1, 10)))


@pytest.mark.parametrize(("client_ip", "expected"), [
    ("192.168.1.55", "192.168.1.0/24"), ("10.2.3.4", "10.2.3.0/24"), ("100.64.1.9", "100.64.1.0/24"),
    ("172.17.0.1", None), ("192.168.65.1", None), ("127.0.0.1", None), ("203.0.113.5", None), ("testclient", None), (None, None),
])
def test_default_scan_cidr(client_ip, expected):
    assert default_scan_cidr(client_ip) == expected


def test_scan_classifies_vlc_and_kodi_on_a_local_server():
    async def run():
        async def vlc_handler(reader, writer):
            await reader.read(1024)
            writer.write(b"HTTP/1.0 403 Forbidden\r\nContent-Type: text/html\r\nContent-Length: 0\r\n\r\n")
            await writer.drain(); writer.close()

        async def kodi_handler(reader, writer):
            await reader.read(1024)
            writer.write(b"HTTP/1.0 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Kodi\"\r\nContent-Length: 0\r\n\r\n")
            await writer.drain(); writer.close()

        vlc = await asyncio.start_server(vlc_handler, "127.0.0.1", 0)
        kodi = await asyncio.start_server(kodi_handler, "127.0.0.1", 0)
        vlc_port = vlc.sockets[0].getsockname()[1]
        kodi_port = kodi.sockets[0].getsockname()[1]
        try:
            outcome = await scan_network(ipaddress.ip_network("127.0.0.1/32"), [vlc_port, kodi_port, 1], timeout_ms=500)
        finally:
            vlc.close(); kodi.close()
        kinds = {(h.host, h.port): h.kind for h in outcome.hits}
        assert kinds[("127.0.0.1", vlc_port)] == "vlc"
        assert kinds[("127.0.0.1", kodi_port)] == "kodi"
        assert ("127.0.0.1", 1) not in kinds
        assert outcome.scanned == 3
    asyncio.run(run())


def test_scan_stops_connecting_once_the_budget_is_spent(monkeypatch):
    """The deadline has to be checked after the semaphore: asyncio.gather runs
    every queued coroutine's first step in one loop iteration, so a check before
    the semaphore is always made while the whole budget is still unspent."""
    async def slow_open(host, port, timeout):
        await asyncio.sleep(0.05)
        return False

    monkeypatch.setattr(scan, "_tcp_open", slow_open)
    network = ipaddress.ip_network("192.168.1.0/28")  # 14 hosts
    outcome = asyncio.run(scan_network(network, [8080], concurrency=2, budget_s=0.15))
    assert 2 <= outcome.scanned < 14
    assert outcome.hits == []


def test_classify_gives_up_on_open_ports_once_the_budget_is_spent():
    """Classification is two HTTP requests per open port; on a dense network it
    is the phase most likely to run past the budget, so it honours it too."""
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"apiversion": 3})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        spent = scan.classify("192.168.1.9", 8080, client, deadline=time.monotonic() - 1)
        assert spent.kind == "unknown" and seen == []
        fresh = scan.classify("192.168.1.9", 8080, client, deadline=time.monotonic() + 30)
        assert fresh.kind == "vlc" and len(seen) == 1


def test_scan_connect_timeouts_shrink_to_fit_the_budget(monkeypatch):
    """A batch small enough to fit the concurrency limit clears the deadline
    check together, so the budget only holds if each connect is capped by the
    time left too: 14 hosts, 128 slots, a 2 s connect timeout, 0.2 s of budget."""
    async def never_answers(host, port):
        await asyncio.sleep(30)

    monkeypatch.setattr(asyncio, "open_connection", never_answers)
    network = ipaddress.ip_network("192.168.1.0/28")  # 14 hosts, one batch
    started = time.monotonic()
    outcome = asyncio.run(scan_network(network, [8080], timeout_ms=2000, budget_s=0.2))
    elapsed = time.monotonic() - started
    assert outcome.scanned == 14 and outcome.hits == []
    assert elapsed < 1.0, f"scan ran {elapsed:.2f}s against a 0.2s budget"
    assert outcome.duration_ms < 1000


def test_classify_caps_each_request_at_the_time_left():
    """Classification is two requests of 2 s read / 1 s connect per open port;
    against a nearly spent budget each one is cut down to the time left."""
    timeouts = []

    def handler(request):
        timeouts.append(request.extensions["timeout"])
        return httpx.Response(404)

    with httpx.Client(
        transport=httpx.MockTransport(handler), timeout=httpx.Timeout(2.0, connect=1.0)
    ) as client:
        scan.classify("192.168.1.9", 8080, client, deadline=time.monotonic() + 0.05)
        assert len(timeouts) == 2
        assert all(t["read"] <= 0.05 and t["connect"] <= 0.05 for t in timeouts)
        timeouts.clear()
        scan.classify("192.168.1.9", 8080, client)  # no budget: the client's own timeout
        assert [t["read"] for t in timeouts] == [2.0, 2.0]
    # The budget can lapse between the deadline check and the request; httpx
    # rejects a negative timeout with a ValueError that no handler here catches.
    lapsed = scan._capped_timeout(time.monotonic() - 5)["timeout"]
    assert lapsed.read == 0.0 and lapsed.connect == 0.0


def test_classify_brackets_an_ipv6_host():
    """`http://fd00::1:8080` is not a URL: httpx raises InvalidURL, which is not
    an httpx.HTTPError, so it escapes classify()'s handlers and 500s the scan.
    The hit keeps the bare address — the Add dialog prefills from it."""
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"apiversion": 3})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        hit = scan.classify("fd00::1", 8080, client)
    assert hit.kind == "vlc" and hit.host == "fd00::1"
    assert seen == ["http://[fd00::1]:8080/requests/status.json"]


def test_scan_identifies_players_on_an_ipv6_network(monkeypatch):
    """fc00::/7 is an accepted, documented scan range, so an IPv6 network with an
    open port has to come back as hits rather than as an unhandled error."""
    async def always_open(host, port, timeout):
        return True

    monkeypatch.setattr(scan, "_tcp_open", always_open)

    def handler(request):
        return httpx.Response(401, headers={"WWW-Authenticate": 'Basic realm="Kodi"'})

    outcome = asyncio.run(
        scan_network(
            ipaddress.ip_network("fd00::/126"),
            [8080],
            client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
        )
    )
    assert [h.host for h in outcome.hits] == ["fd00::1", "fd00::2", "fd00::3"]
    assert {h.kind for h in outcome.hits} == {"kodi"}


def test_classify_refuses_addresses_the_lan_guard_blocks():
    """classify() is an outbound request builder like the drivers, so it runs the
    same guard: fd00:ec2::254 (the cloud metadata endpoint) is inside fc00::/7."""
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"apiversion": 3})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        hit = scan.classify("fd00:ec2::254", 8080, client)
    assert hit.kind == "unknown" and seen == []


def test_scan_skips_addresses_the_lan_guard_blocks(monkeypatch):
    """validate_scan_request accepts a /122 around fd00:ec2::254 — every address
    in it is private — so the scan itself must leave the metadata endpoint alone."""
    validate_scan_request("fd00:ec2::240/122", [8080])  # accepted, by design
    connects = []

    async def note(host, port, timeout):
        connects.append(host)
        return False

    monkeypatch.setattr(scan, "_tcp_open", note)
    outcome = asyncio.run(scan_network(ipaddress.ip_network("fd00:ec2::250/125"), [8080]))
    assert "fd00:ec2::254" not in connects
    assert connects and outcome.scanned == len(connects)

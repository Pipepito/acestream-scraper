"""Network scan for VLC/Kodi web interfaces: validation, defaults, classification (spec 6.1)."""
import asyncio
import ipaddress

import pytest

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

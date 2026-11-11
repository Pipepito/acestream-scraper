"""Ports for programs outside the container: the WARP SOCKS port and its wiring."""
import asyncio
import importlib.util
import os
from pathlib import Path
import socket
import struct
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "docker" / "scripts"
LOOPBACK = "127.0.0.0/8"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


warp_socks = _load("warp_socks", "warp-socks.py")


def _socks_request(port, host, target_port, *, command=1):
    """Greet, send one request and return the reply code (None if closed)."""
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(b"\x05\x01\x00")
        if s.recv(2) != b"\x05\x00":
            return None
        try:
            address = b"\x01" + socket.inet_aton(host)
        except OSError:
            address = b"\x03" + bytes([len(host)]) + host.encode()
        s.sendall(bytes([5, command, 0]) + address + struct.pack("!H", target_port))
        reply = s.recv(10)
        if not reply:
            return None
        if reply[1] == warp_socks.REP_OK:
            s.sendall(b"hola")
            return s.recv(100)
        return reply[1]


async def _serve(handle):
    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


async def _echo_server():
    async def echo(reader, writer):
        writer.write(b"echo:" + await reader.read(100))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    return await _serve(echo)


async def _close(*servers):
    for server in servers:
        server.close()
        await server.wait_closed()


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "10.1.2.3", "192.168.1.10",
                                  "169.254.169.254", "::1", "fd00::1"])
def test_socks_refuses_destinations_that_are_not_public(host):
    async def scenario():
        server, port = await _serve(warp_socks.handler(warp_socks.parse_networks(LOOPBACK)))
        try:
            return await asyncio.to_thread(_socks_request, port, host, 80)
        finally:
            await _close(server)

    if ":" in host:
        assert asyncio.run(warp_socks.public_address(host, 80)) is None
    else:
        assert asyncio.run(scenario()) == warp_socks.REP_NOT_ALLOWED


def test_socks_reports_a_name_that_does_not_resolve_as_unreachable():
    """Not as a refused destination: while WARP is down DNS fails too."""
    async def scenario():
        server, port = await _serve(warp_socks.handler(warp_socks.parse_networks(LOOPBACK)))
        try:
            return await asyncio.to_thread(_socks_request, port, "name.invalid", 80)
        finally:
            await _close(server)

    assert asyncio.run(scenario()) == warp_socks.REP_UNREACHABLE


def test_socks_public_address_takes_the_first_global_answer():
    assert asyncio.run(warp_socks.public_address("192.0.2.1", 80)) is None  # documentation range
    assert asyncio.run(warp_socks.public_address("1.1.1.1", 80)) == "1.1.1.1"


def test_socks_relays_to_the_resolved_public_address(monkeypatch):
    """The upstream connection goes to the address that passed the check."""
    async def scenario():
        echo, echo_port = await _echo_server()

        async def resolved(host, port):
            assert (host, port) == ("example.com", echo_port)
            return "127.0.0.1"   # stands in for a public answer
        monkeypatch.setattr(warp_socks, "public_address", resolved)
        server, port = await _serve(warp_socks.handler(warp_socks.parse_networks(LOOPBACK)))
        try:
            return await asyncio.to_thread(_socks_request, port, "example.com", echo_port)
        finally:
            await _close(server, echo)

    assert asyncio.run(scenario()) == b"echo:hola"


def test_socks_closes_clients_outside_the_allowed_networks():
    async def scenario():
        server, port = await _serve(warp_socks.handler(warp_socks.parse_networks("10.0.0.0/8")))
        try:
            def greet():
                with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
                    s.sendall(b"\x05\x01\x00")
                    try:
                        return s.recv(2)
                    except ConnectionResetError:   # closed with the greeting unread
                        return b""
            return await asyncio.to_thread(greet)
        finally:
            await _close(server)

    assert asyncio.run(scenario()) == b""


def test_socks_rejects_commands_other_than_connect():
    async def scenario():
        server, port = await _serve(warp_socks.handler(warp_socks.parse_networks(LOOPBACK)))
        try:
            return await asyncio.to_thread(_socks_request, port, "1.1.1.1", 80, command=2)
        finally:
            await _close(server)

    assert asyncio.run(scenario()) == warp_socks.REP_CMD_UNSUPPORTED


def test_client_networks_accept_ipv4_mapped_peers():
    networks = warp_socks.parse_networks("192.168.0.0/16")
    assert warp_socks.client_allowed(("::ffff:192.168.1.5", 1, 0, 0), networks)
    assert not warp_socks.client_allowed(("203.0.113.9", 1), networks)


# --- wiring -----------------------------------------------------------------

def _entrypoint(tmp_path, **extra):
    env = {**os.environ, "DATABASE_URL": "sqlite:///" + str(tmp_path / "scraper.db"),
           "LOG_DIR": str(tmp_path / "logs"), "LOGROTATE_DIR": str(tmp_path / "rotation"),
           "SUPERVISOR_RUN_DIR": str(tmp_path / "run"), "ENABLE_WARP": "false",
           "ENABLE_ACESTREAM_ENGINE": "false", "ENABLE_ACEXY": "false",
           "ENABLE_IPFS": "false", "ENABLE_ZERONET": "false", **extra}
    return subprocess.run(["bash", str(ROOT / "entrypoint.sh"), "true"], env=env,
                          text=True, capture_output=True, timeout=15)


def test_entrypoint_rejects_a_socks_port_that_is_not_a_number(tmp_path):
    result = _entrypoint(tmp_path, WARP_SOCKS_PORT="10800x")
    assert result.returncode != 0
    assert "WARP_SOCKS_PORT must be a port number" in result.stdout + result.stderr


def test_entrypoint_skips_the_socks_port_without_the_full_tunnel(tmp_path):
    result = _entrypoint(tmp_path, WARP_SOCKS_PORT="1080")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "not starting the SOCKS port" in result.stdout + result.stderr
    assert not (tmp_path / "run" / "warp-socks.pid").exists()


def test_socks_port_starts_with_the_network_services_under_the_supervisor():
    """Not from warp-setup.sh: the WARP coordinator ends each configuration
    attempt by killing its whole process group, so a helper started there
    would not survive it."""
    entrypoint = (ROOT / "entrypoint.sh").read_text()
    services = entrypoint[entrypoint.index("start_network_services() {"):]
    services = services[:services.index("network_services_started=true")]
    assert 'start_helper "WARP-SOCKS"' in services
    assert "--allow $(printf '%q' \"$TUNER_ALLOWED_NETWORKS\")" in services
    assert "warp-socks" not in (ROOT / "warp-setup.sh").read_text()
    assert "docker/scripts/warp-socks.py /usr/local/bin/warp-socks.py" in (ROOT / "Dockerfile").read_text()

"""Wire-protocol regressions; actual libc calls also run in the ARM Docker test."""
import importlib.util
from pathlib import Path
import socket
import struct
import threading

import pytest


@pytest.fixture
def proxy():
    path = Path(__file__).resolve().parents[2] / "docker/scripts/acestream-android/bionic_dns_proxy.py"
    spec = importlib.util.spec_from_file_location("bionic_dns_proxy_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("family,address", [
    (socket.AF_INET, ("192.0.2.253", 6881)),
    (socket.AF_INET6, ("2001:db8::253", 6881, 42, 3)),
])
def test_addrinfo_preserves_requested_service_type_and_all_addresses(proxy, monkeypatch, family, address):
    calls = []

    def lookup(*args):
        calls.append(args)
        return [(family, socket.SOCK_DGRAM, 17, "engine.test", address)] * 2

    monkeypatch.setattr(proxy.socket, "getaddrinfo", lookup)
    result = proxy.response(f"getaddrinfo engine.test 6881 2 {family} 2 17 0".encode())
    assert calls == [("engine.test", "6881", family, 2, 17, 2)]
    assert result[:4] == b"222\0"
    offset = 4
    for _ in range(2):
        more, flags, got_family, kind, protocol, size = struct.unpack_from("!6I", result, offset)
        assert (more, flags, got_family, kind, protocol) == (1, 2, family, 2, 17)
        offset += 24
        packed = result[offset:offset + size]
        assert struct.unpack_from("=H", packed)[0] == family
        assert struct.unpack_from("!H", packed, 2)[0] == 6881
        if family == socket.AF_INET:
            assert size == 16
            assert packed[4:8] == socket.inet_pton(family, address[0])
        else:
            assert size == 28
            assert struct.unpack_from("!I", packed, 4)[0] == 42
            assert packed[8:24] == socket.inet_pton(family, address[0])
            assert struct.unpack_from("=I", packed, 24)[0] == 3
        offset += size
        name_size = struct.unpack_from("!I", result, offset)[0]
        assert result[offset + 4:offset + 4 + name_size] == b"engine.test\0"
        offset += 4 + name_size
    assert result[offset:] == b"\0" * 4


def test_null_service_and_absent_hints(proxy, monkeypatch):
    calls = []

    def lookup(*args):
        calls.append(args)
        return [(socket.AF_INET, 1, 6, "", ("192.0.2.1", 0))]

    monkeypatch.setattr(proxy.socket, "getaddrinfo", lookup)
    assert proxy.response(b"getaddrinfo engine.test ^ -1 -1 -1 -1 0").startswith(b"222\0")
    assert calls == [("engine.test", None, 0, 0, 0, 0)]


def test_hostent_keeps_aliases_and_addresses(proxy, monkeypatch):
    monkeypatch.setattr(proxy.socket, "gethostbyaddr", lambda _: (
        "engine.test", ["alias.test"], ["192.0.2.1", "192.0.2.2"]))
    assert proxy.response(b"gethostbyaddr 192.0.2.1 4 2 0") == (
        b"222\0" + struct.pack("!I", 12) + b"engine.test\0" +
        struct.pack("!I", 11) + b"alias.test\0" + struct.pack("!4I", 0, 2, 4, 4) +
        socket.inet_aton("192.0.2.1") + struct.pack("!I", 4) +
        socket.inet_aton("192.0.2.2") + struct.pack("!I", 0))


def test_hosts_aliases_use_numeric_lookup_and_preserve_family(proxy, monkeypatch, tmp_path):
    hosts = tmp_path / "hosts"
    hosts.write_text("bad entry\n192.0.2.1 engine.test alias.test # comment\n2001:db8::1 engine.test\n")
    entries = proxy._hosts(hosts)
    monkeypatch.setattr(proxy, "_hosts", lambda: entries)
    calls = []

    def numeric_lookup(host, service, family, kind, protocol, flags):
        calls.append(host)
        assert flags & socket.AI_NUMERICHOST
        return [(family, kind, protocol, host, (host, int(service)))]

    monkeypatch.setattr(proxy.socket, "getaddrinfo", numeric_lookup)
    rows = proxy._getaddrinfo("ALIAS.TEST", "443", socket.AF_INET, 1, 6, socket.AI_CANONNAME)
    assert rows == [(socket.AF_INET, 1, 6, "engine.test", ("192.0.2.1", 443))]
    assert calls == ["192.0.2.1"]
    with pytest.raises(socket.gaierror):
        proxy._getaddrinfo("alias.test", "443", socket.AF_INET6)


def test_dns_retry_error_is_not_replaced_with_nxdomain(proxy, monkeypatch):
    def retry(query):
        raise socket.gaierror(socket.EAI_AGAIN, "temporary failure")

    monkeypatch.setattr(proxy, "response", retry)
    server, client = socket.socketpair()
    worker = threading.Thread(target=proxy.serve_client, args=(server,))
    worker.start()
    with client:
        client.settimeout(2)
        client.sendall(b"query\0")
        result = b""
        while len(result) < 12:
            result += client.recv(12)
        assert result == b"401\0" + struct.pack("!I", 4) + struct.pack("=i", socket.EAI_AGAIN)
    worker.join(timeout=3)
    assert not worker.is_alive()


@pytest.mark.parametrize("query", [b"\0", b"unsupported\0", b"getaddrinfo short\0", b"x" * 4097,
                                     b"gethostbyaddr invalid 4 2 0\0", b"\xff\0"])
def test_bad_client_gets_bounded_failure(proxy, query):
    server, client = socket.socketpair()
    worker = threading.Thread(target=proxy.serve_client, args=(server,))
    worker.start()
    try:
        with client:
            client.settimeout(2)
            client.sendall(query)
            response = bytearray()
            while len(response) < 12:
                part = client.recv(12)
                assert part
                response.extend(part)
            assert bytes(response) == b"401\0" + struct.pack("!I", 4) + struct.pack("=i", 7)
    finally:
        worker.join(timeout=3)
    assert not worker.is_alive()


def test_fragmented_request_and_disconnecting_client(proxy, monkeypatch):
    monkeypatch.setattr(proxy, "response", lambda query: b"answer:" + query)
    for disconnect in (False, True):
        server, client = socket.socketpair()
        worker = threading.Thread(target=proxy.serve_client, args=(server,))
        worker.start()
        with client:
            client.settimeout(2)
            client.sendall(b"getaddr")
            client.sendall(b"info example.test")
            if not disconnect:
                client.sendall(b"\0")
                assert client.recv(1024) == b"answer:getaddrinfo example.test"
        worker.join(timeout=3)
        assert not worker.is_alive()

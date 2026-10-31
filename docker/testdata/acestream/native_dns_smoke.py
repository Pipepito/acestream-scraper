"""Offline integration check, executed by the actual installed bionic Python.

No Python lookup patch can make these assertions pass on its own: _socket and
ctypes call libc directly. Run in a disposable container with no network.
"""
import _socket
import ctypes
import os
import socket
import tempfile
import threading

import dns.message
import dns.rcode
import dns.resolver
import dns.rrset

from bionic_dns import container_resolver, start_shared_dns
from bionic_dns_proxy import dnsproxyd_listener


def dns_server(server, ipv4):
    while True:
        wire, peer = server.recvfrom(4096)
        request = dns.message.from_wire(wire)
        reply = dns.message.make_response(request)
        question = request.question[0]
        if question.name.to_text() == "missing.test.":
            reply.set_rcode(dns.rcode.NXDOMAIN)
        else:
            values = {1: ipv4, 28: "2001:db8::253", 12: "engine.test."}
            value = values.get(question.rdtype)
            if value:
                reply.answer.append(dns.rrset.from_text(
                    question.name, 0, "IN", question.rdtype, value))
        server.sendto(reply.to_wire(), peer)


servers = []
port = 0
for ip, answer in (("127.0.0.1", "192.0.2.1"), ("127.0.0.2", "192.0.2.2")):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((ip, port))
    port = server.getsockname()[1]
    servers.append(server)
    threading.Thread(target=dns_server, args=(server, answer), daemon=True).start()

with tempfile.TemporaryDirectory() as state:
    path = os.path.join(state, "resolv.conf")

    def config(content):
        with open(path, "w") as handle:
            handle.write(content)

    config("nameserver 127.0.0.1\n")
    resolver = container_resolver(dns.resolver.Resolver, print, path)
    resolver.port = port
    dns.resolver.override_system_resolver(resolver)
    start_shared_dns(dnsproxyd_listener, resolver)

    libc = ctypes.CDLL("libc.so")
    libc.getaddrinfo.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
                                 ctypes.POINTER(ctypes.c_void_p)]
    libc.getaddrinfo.restype = ctypes.c_int
    libc.freeaddrinfo.argtypes = [ctypes.c_void_p]
    libc.freeaddrinfo.restype = None
    result = ctypes.c_void_p()
    assert libc.getaddrinfo(b"engine.test", b"443", None, ctypes.byref(result)) == 0
    libc.freeaddrinfo(result)
    with open("/system/etc/hosts", "a") as hosts:
        hosts.write("\n192.0.2.253 local-engine.test local-alias.test\n")
    assert _socket.gethostbyname("local-alias.test") == "192.0.2.253"
    assert _socket.gethostbyaddr("192.0.2.253")[0] == "local-engine.test"

    for nameserver, expected in (("127.0.0.1", "192.0.2.1"), ("127.0.0.2", "192.0.2.2")):
        config("nameserver {}\n".format(nameserver))
        for kind, protocol in ((socket.SOCK_STREAM, 6), (socket.SOCK_DGRAM, 17)):
            rows = _socket.getaddrinfo("engine.test", 6881, socket.AF_INET, kind)
            assert rows == [(socket.AF_INET, kind, protocol, "", (expected, 6881))], rows
        assert _socket.gethostbyname("engine.test") == expected
        assert _socket.gethostbyaddr(expected)[0] == "engine.test"
        config("")  # Partial WARP rewrite retains the last valid nameserver.
        assert _socket.gethostbyname("engine.test") == expected

    rows = _socket.getaddrinfo("engine.test", 443, socket.AF_INET6, socket.SOCK_STREAM)
    assert rows == [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::253", 443, 0, 0))], rows
    assert _socket.getaddrinfo("127.0.0.1", 443, socket.AF_INET, socket.SOCK_STREAM)[0][4] == ("127.0.0.1", 443)
    try:
        _socket.getaddrinfo("missing.test", 443)
        raise AssertionError("NXDOMAIN unexpectedly resolved")
    except socket.gaierror:
        pass
    # A negative response must not terminate the shared listener.
    assert _socket.gethostbyname("engine.test") == "192.0.2.2"
    print("native bionic DNS smoke passed", flush=True)

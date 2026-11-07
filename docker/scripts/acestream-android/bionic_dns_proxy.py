"""Android netd wire protocol backed by the bootstrap's dnspython overrides.

The pinned upstream listener hard-codes IPv4/TCP/port 80. Native callers need
the requested service, family and socket type, plus hostent replies for the
older gethostbyname/gethostbyaddr APIs. Never call unpatched libc for a name
here: that would recurse into this listener.
"""
import ipaddress
import socket
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor


def _word(value):
    return struct.pack("!I", value)


def _string(value):
    data = value.encode("utf-8") + b"\0" if value else b""
    return _word(len(data)) + data


def _hosts(path="/system/etc/hosts"):
    # Preserve bionic's local host aliases when native calls use the proxy.
    try:
        with open(path) as handle:
            content = handle.read(65537)
    except OSError:
        return []
    if len(content) > 65536:
        return []
    entries = []
    for line in content.splitlines():
        fields = line.split("#", 1)[0].split()
        if len(fields) < 2:
            continue
        try:
            ipaddress.ip_address(fields[0])
        except ValueError:
            continue
        entries.append(fields)
    return entries


def _getaddrinfo(host, service, family=0, kind=0, protocol=0, flags=0):
    matches = [entry for entry in _hosts() if host and host.lower() in
               [name.lower() for name in entry[1:]]]
    if not matches or flags & socket.AI_NUMERICHOST:
        return socket.getaddrinfo(host, service, family, kind, protocol, flags)
    records = []
    for ip, canonical, *_ in matches:
        ip_family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        if family not in (0, ip_family):
            continue
        for af, st, proto, _, addr in socket.getaddrinfo(
                ip, service, ip_family, kind, protocol, flags | socket.AI_NUMERICHOST):
            records.append((af, st, proto, canonical if flags & socket.AI_CANONNAME else "", addr))
    if not records:
        raise socket.gaierror(socket.EAI_NONAME, "no address in requested family")
    return records


def _hostent(name, aliases, addresses, family):
    packed = [socket.inet_pton(family, ip) for ip in addresses[:64]]
    if not packed:
        raise ValueError("no addresses")
    return (b"222\0" + _string(name) +
            b"".join(_string(alias) for alias in aliases[:64]) + _word(0) +
            _word(family) + _word(len(packed[0])) +
            b"".join(_word(len(ip)) + ip for ip in packed) + _word(0))


def response(query):
    fields = query.decode("ascii").split()
    if fields[0] == "getaddrinfo" and len(fields) == 8:
        host, service = (None if value == "^" else value for value in fields[1:3])
        flags, family, kind, protocol = (max(0, int(value)) for value in fields[3:7])
        records = _getaddrinfo(host, service, family, kind, protocol, flags)
        if not records:
            raise ValueError("no addresses")
        result = [b"222\0"]
        for family, kind, protocol, canonname, address in records[:64]:
            # sockaddr family/scope are native-endian; port/flowinfo are network-endian.
            packed = struct.pack("=H", family) + struct.pack("!H", address[1])
            if family == socket.AF_INET:
                packed += socket.inet_pton(family, address[0]) + b"\0" * 8
            elif family == socket.AF_INET6:
                packed += struct.pack("!I", address[2])
                packed += socket.inet_pton(family, address[0]) + struct.pack("=I", address[3])
            else:
                raise ValueError("unsupported address family")
            result.extend((_word(1), _word(flags), _word(family), _word(kind),
                           _word(protocol), _word(len(packed)), packed, _string(canonname)))
        return b"".join(result) + _word(0)
    if fields[0] == "gethostbyname" and len(fields) == 4:
        family = int(fields[3])
        records = _getaddrinfo(fields[2], None, family, socket.SOCK_STREAM,
                               0, socket.AI_CANONNAME)
        addresses = list(dict.fromkeys(record[4][0] for record in records))
        return _hostent(records[0][3] or fields[2], [], addresses, family)
    if fields[0] == "gethostbyaddr" and len(fields) == 5:
        family = int(fields[3])
        if len(socket.inet_pton(family, fields[1])) != int(fields[2]):
            raise ValueError("invalid address length")
        matches = [entry for entry in _hosts()
                   if ipaddress.ip_address(entry[0]) == ipaddress.ip_address(fields[1])]
        if matches:
            addresses, name, aliases = [fields[1]], matches[0][1], matches[0][2:]
        else:
            name, aliases, addresses = socket.gethostbyaddr(fields[1])
        return _hostent(name, aliases, addresses, family)
    raise ValueError("unsupported DNS request")


def serve_client(client):
    with client:
        client.settimeout(5)
        try:
            query = bytearray()
            deadline = time.monotonic() + 5
            while b"\0" not in query:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("DNS request deadline exceeded")
                client.settimeout(remaining)
                part = client.recv(1024)
                if not part:
                    return
                query.extend(part)
                if len(query) > 4096:
                    raise ValueError("DNS request too long")
            reply = response(bytes(query).split(b"\0", 1)[0])
        except socket.gaierror as exc:
            reply = b"401\0" + _word(4) + struct.pack("=i", exc.errno)
        except (OSError, ValueError, IndexError, UnicodeError):
            # Android's negative result: payload length, native-endian EAI_NODATA.
            reply = b"401\0" + _word(4) + struct.pack("=i", 7)
        try:
            client.sendall(reply)
        except OSError:
            pass  # A timed-out caller must not kill the shared listener.


def dnsproxyd_listener(resolver):
    # The public socket functions have already been overridden by dnspython.
    # Bound DNS work and concurrent clients; never queue unbounded requests.
    resolver.lifetime = 3
    slots = threading.BoundedSemaphore(4)

    def handle(client):
        try:
            serve_client(client)
        finally:
            slots.release()

    with ThreadPoolExecutor(max_workers=4) as workers:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind("/dev/socket/dnsproxyd")
            server.listen(16)
            while True:
                client, _ = server.accept()
                if slots.acquire(blocking=False):
                    workers.submit(handle, client)
                else:
                    client.close()

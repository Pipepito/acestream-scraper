#!/usr/bin/env python3
"""SOCKS5 port (no auth, CONNECT only) whose traffic leaves through WARP.

In full tunnel mode everything the container sends leaves through WARP, but
other programs (a media centre add-on, another container) cannot use that
tunnel. warp-cli's own proxy mode would give them a SOCKS port at the price of
switching the tunnel off for the scraper. This server keeps the tunnel and
offers the port: what it relays is sent from inside the container, so it
leaves through WARP too, and the kill switch blocks it while WARP is down.

Limits, because the port has no authentication:
- clients only from --allow networks (the entrypoint passes
  TUNER_ALLOWED_NETWORKS, private ranges by default);
- destinations only on public addresses: names are resolved here (socks5h)
  and a name or address that is loopback, private, link-local or otherwise
  not global is refused, so the port cannot reach the container's own
  services or the local network.
Only CONNECT is supported; BIND and UDP ASSOCIATE are refused.

    warp-socks.py --port 1080 [--host 0.0.0.0] [--allow 10.0.0.0/8,...]
"""
import argparse
import asyncio
import ipaddress
import logging
import socket
import struct

log = logging.getLogger("warp-socks")

VERSION = 5
NO_AUTH = 0
NO_ACCEPTABLE = 0xFF
CONNECT = 1
ATYP_IPV4, ATYP_DOMAIN, ATYP_IPV6 = 1, 3, 4
REP_OK, REP_FAILURE, REP_NOT_ALLOWED, REP_UNREACHABLE, REP_REFUSED = 0, 1, 2, 4, 5
REP_CMD_UNSUPPORTED, REP_ATYP_UNSUPPORTED = 7, 8
CONNECT_TIMEOUT = 30
HANDSHAKE_TIMEOUT = 10
DEFAULT_ALLOWED = ("127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,"
                   "::1/128,fc00::/7,fe80::/10")


def parse_networks(text):
    return [ipaddress.ip_network(part.strip(), strict=False) for part in text.split(",") if part.strip()]


def client_allowed(peer, networks):
    try:
        address = ipaddress.ip_address(peer[0])
    except (TypeError, ValueError, IndexError):
        return False
    if address.version == 6 and address.ipv4_mapped:
        address = address.ipv4_mapped
    return any(address in network for network in networks)


async def public_address(host, port):
    """The first global address `host` resolves to, or None.

    A name that does not resolve raises socket.gaierror (while WARP is down
    the kill switch blocks DNS too), so it is not reported as a refusal."""
    infos = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if address.version == 6 and address.ipv4_mapped:
            address = address.ipv4_mapped
        if address.is_global:
            return str(address)
    return None


async def _read_request(reader):
    """Return (host, port) from a CONNECT request, or raise ValueError(rep)."""
    ver, cmd, _rsv, atyp = await reader.readexactly(4)
    if ver != VERSION:
        raise ValueError(REP_FAILURE)
    if atyp == ATYP_IPV4:
        host = str(ipaddress.IPv4Address(await reader.readexactly(4)))
    elif atyp == ATYP_IPV6:
        host = str(ipaddress.IPv6Address(await reader.readexactly(16)))
    elif atyp == ATYP_DOMAIN:
        length = (await reader.readexactly(1))[0]
        host = (await reader.readexactly(length)).decode("idna")
    else:
        raise ValueError(REP_ATYP_UNSUPPORTED)
    port = struct.unpack("!H", await reader.readexactly(2))[0]
    if cmd != CONNECT:
        raise ValueError(REP_CMD_UNSUPPORTED)
    return host, port


def _reply(rep, bound=("0.0.0.0", 0)):
    try:
        addr = ipaddress.ip_address(bound[0])
    except ValueError:
        addr = ipaddress.IPv4Address("0.0.0.0")
    atyp = ATYP_IPV6 if addr.version == 6 else ATYP_IPV4
    return bytes([VERSION, rep, 0, atyp]) + addr.packed + struct.pack("!H", bound[1])


async def _pipe(reader, writer):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        try:
            writer.close()
        except Exception:  # noqa: BLE001
            pass


async def _handshake(reader, writer):
    """Agree on no authentication and read the request: (host, port) or None."""
    ver, nmethods = await reader.readexactly(2)
    methods = await reader.readexactly(nmethods)
    if ver != VERSION or NO_AUTH not in methods:
        writer.write(bytes([VERSION, NO_ACCEPTABLE]))
        await writer.drain()
        return None
    writer.write(bytes([VERSION, NO_AUTH]))
    await writer.drain()
    try:
        return await _read_request(reader)
    except ValueError as e:
        writer.write(_reply(e.args[0]))
        await writer.drain()
        return None


def handler(networks):
    async def handle(reader, writer):
        peer = writer.get_extra_info("peername")
        try:
            if not client_allowed(peer, networks):
                log.info("refused client %s: not in the allowed networks", peer[0] if peer else "?")
                return
            request = await asyncio.wait_for(_handshake(reader, writer), HANDSHAKE_TIMEOUT)
            if request is None:
                return
            host, port = request
            try:
                address = await public_address(host, port)
            except socket.gaierror as e:
                log.info("%s -> %s:%s failed: the name does not resolve (%s)", peer[0], host, port, e)
                writer.write(_reply(REP_UNREACHABLE))
                await writer.drain()
                return
            if address is None:
                log.info("%s -> %s:%s refused: no public address", peer[0], host, port)
                writer.write(_reply(REP_NOT_ALLOWED))
                await writer.drain()
                return
            try:
                up_reader, up_writer = await asyncio.wait_for(
                    asyncio.open_connection(address, port), CONNECT_TIMEOUT)
            except (asyncio.TimeoutError, OSError) as e:
                rep = REP_REFUSED if isinstance(e, ConnectionRefusedError) else REP_UNREACHABLE
                log.info("%s -> %s:%s failed: %s", peer[0], host, port, e)
                writer.write(_reply(rep))
                await writer.drain()
                return
            writer.write(_reply(REP_OK, up_writer.get_extra_info("sockname")[:2]))
            await writer.drain()
            await asyncio.gather(_pipe(reader, up_writer), _pipe(up_reader, writer))
        except (asyncio.IncompleteReadError, asyncio.TimeoutError, ConnectionError):
            pass
        finally:
            try:
                writer.close()
            except Exception:  # noqa: BLE001
                pass
    return handle


async def serve(host, port, networks):
    server = await asyncio.start_server(handler(networks), host, port)
    log.info("SOCKS5 listening on %s:%s", host, port)
    async with server:
        await server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--allow", default=DEFAULT_ALLOWED,
                        help="comma-separated client networks")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s warp-socks: %(message)s")
    asyncio.run(serve(args.host, args.port, parse_networks(args.allow)))


if __name__ == "__main__":
    main()

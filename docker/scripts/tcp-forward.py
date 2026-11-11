#!/usr/bin/env python3
"""Forward a TCP port to another address, byte for byte.

The embedded Tor listens on 127.0.0.1:9050 inside the container, which a
published port cannot reach. This exposes it on another port of the
container's interfaces, for clients from --allow networks only (the
entrypoint passes TUNER_ALLOWED_NETWORKS, private ranges by default):

    tcp-forward.py --port 9150 --to 127.0.0.1:9050 [--allow 10.0.0.0/8,...]
"""
import argparse
import asyncio
import ipaddress
import logging

log = logging.getLogger("tcp-forward")

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


def handler(target_host, target_port, networks):
    async def handle(reader, writer):
        peer = writer.get_extra_info("peername")
        if not client_allowed(peer, networks):
            log.info("refused client %s: not in the allowed networks", peer[0] if peer else "?")
            writer.close()
            return
        try:
            up_reader, up_writer = await asyncio.open_connection(target_host, target_port)
        except OSError as e:
            log.info("cannot reach %s:%s: %s", target_host, target_port, e)
            writer.close()
            return
        await asyncio.gather(_pipe(reader, up_writer), _pipe(up_reader, writer))
    return handle


async def serve(host, port, target_host, target_port, networks):
    server = await asyncio.start_server(handler(target_host, target_port, networks), host, port)
    log.info("forwarding %s:%s -> %s:%s", host, port, target_host, target_port)
    async with server:
        await server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--to", required=True, help="host:port")
    parser.add_argument("--allow", default=DEFAULT_ALLOWED,
                        help="comma-separated client networks")
    args = parser.parse_args()
    target_host, _, target_port = args.to.rpartition(":")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s tcp-forward: %(message)s")
    asyncio.run(serve(args.host, args.port, target_host, int(target_port),
                      parse_networks(args.allow)))


if __name__ == "__main__":
    main()

"""Bounded, process-local Docker proxy defaults; no Docker socket or DNS."""
from functools import lru_cache
import ipaddress
import json
from pathlib import Path
import subprocess
import sys

LOOPBACK = ('127.0.0.1/32', '::1/128')
PRIVATE = tuple(ipaddress.ip_network(value) for value in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7'))


def bridge_peers(interfaces, routes):
    """Trust private veth subnets, excluding every routing gateway.

    A host-network container has physical interfaces, not its own veth. Never
    infer proxy trust from that host's LAN or from a published-port NAT gateway.
    """
    peers = set()
    for interface in interfaces:
        if interface.get('linkinfo', {}).get('info_kind') != 'veth':
            continue
        local_routes = [route for route in routes if route.get('dev') == interface.get('ifname')]
        if not any(route.get('dst') == 'default' and route.get('gateway') for route in local_routes):
            continue
        gateways = [ipaddress.ip_address(route['gateway']) for route in local_routes if route.get('gateway')]
        for address in interface.get('addr_info', []):
            if address.get('scope') != 'global':
                continue
            subnet = ipaddress.ip_interface(f"{address['local']}/{address['prefixlen']}").network
            if not any(subnet.version == private.version and subnet.subnet_of(private) for private in PRIVATE):
                continue
            remaining = [subnet]
            for gateway in gateways:
                remaining = [piece for network in remaining for piece in
                             (network.address_exclude(ipaddress.ip_network(gateway)) if gateway in network else [network])]
            peers.update(str(network) for network in remaining)
    return tuple(sorted(peers))


def _ip_json(*args):
    result = subprocess.run(['ip', '-j', *args], capture_output=True, timeout=1, check=True)
    if len(result.stdout) > 262144:
        raise ValueError('Interface inventory exceeds limit')
    value = json.loads(result.stdout)
    if not isinstance(value, list):
        raise ValueError('Invalid interface inventory')
    return value


@lru_cache(maxsize=1)
def automatic_proxy_peers():
    if sys.platform != 'linux' or not Path('/.dockerenv').is_file():
        return LOOPBACK
    try:
        interfaces = _ip_json('-d', 'address', 'show')
        routes = _ip_json('-4', 'route', 'show') + _ip_json('-6', 'route', 'show')
        return LOOPBACK + bridge_peers(interfaces, routes)
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, KeyError, AttributeError):
        return LOOPBACK

import ipaddress
import subprocess

import pytest

import network_defaults as defaults
from app.middleware.forwarded import parse_trusted
from runtime_config import bootstrap_values


def inventory(kind='veth', address='172.17.0.2', prefix=16):
    return [{'ifname': 'eth0', 'linkinfo': {'info_kind': kind}, 'addr_info': [
        {'local': address, 'prefixlen': prefix, 'scope': 'global'}]}]


def test_docker_peers_exclude_gateways_and_do_not_trust_lan(monkeypatch):
    routes = [{'dev': 'eth0', 'dst': 'default', 'gateway': '172.17.0.1'},
              {'dev': 'eth0', 'dst': '10.0.0.0/8', 'gateway': '172.17.0.3'}]
    peers = defaults.LOOPBACK + defaults.bridge_peers(inventory(), routes)
    monkeypatch.setattr('app.middleware.forwarded.automatic_proxy_peers', lambda: peers)
    trusted = parse_trusted('auto')
    for host in ('127.0.0.1', '::1', '172.17.0.2', '172.17.0.16', '172.17.255.254'):
        assert trusted.contains(host)
    for host in ('172.17.0.1', '172.17.0.3', '172.18.0.16', '192.168.1.245', '8.8.8.8'):
        assert not trusted.contains(host)
    assert not parse_trusted('127.0.0.1').contains('172.17.0.16')


@pytest.mark.parametrize('kind,address', [('bridge', '172.17.0.2'), ('macvlan', '192.168.1.2'), ('', '192.168.1.2'), ('veth', '8.8.8.8')])
def test_physical_host_macvlan_and_public_subnets_are_not_inferred(kind, address):
    assert defaults.bridge_peers(inventory(kind, address), [{'dev': 'eth0', 'dst': 'default', 'gateway': '172.17.0.1'}]) == ()


def test_private_ipv6_bridge_excludes_gateway():
    peers = defaults.bridge_peers(inventory(address='fd12::2', prefix=64),
                                  [{'dev': 'eth0', 'dst': 'default', 'gateway': 'fd12::1'}])
    assert any(ipaddress.ip_address('fd12::16') in ipaddress.ip_network(value) for value in peers)
    assert not any(ipaddress.ip_address('fd12::1') in ipaddress.ip_network(value) for value in peers)


def test_auto_is_default_and_preserves_explicit_environment_and_saved_values():
    assert bootstrap_values({})['FORWARDED_ALLOW_IPS'] == 'auto'
    assert bootstrap_values({'FORWARDED_ALLOW_IPS': '172.17.0.16'})['FORWARDED_ALLOW_IPS'] == '172.17.0.16'
    assert bootstrap_values({'FORWARDED_ALLOW_IPS': 'auto'}, {'FORWARDED_ALLOW_IPS': '127.0.0.1'})['FORWARDED_ALLOW_IPS'] == '127.0.0.1'


def test_detection_is_cached_and_failure_falls_back_to_loopback(monkeypatch):
    defaults.automatic_proxy_peers.cache_clear()
    monkeypatch.setattr(defaults.sys, 'platform', 'linux')
    monkeypatch.setattr(defaults.Path, 'is_file', lambda self: True)
    calls = []
    def fail(*args):
        calls.append(args)
        raise subprocess.TimeoutExpired('ip', 1)
    monkeypatch.setattr(defaults, '_ip_json', fail)
    try:
        assert defaults.automatic_proxy_peers() == defaults.LOOPBACK
        assert defaults.automatic_proxy_peers() == defaults.LOOPBACK
        assert len(calls) == 1
    finally:
        defaults.automatic_proxy_peers.cache_clear()


def test_non_docker_does_not_inspect_host_network(monkeypatch):
    defaults.automatic_proxy_peers.cache_clear()
    monkeypatch.setattr(defaults.Path, 'is_file', lambda self: False)
    monkeypatch.setattr(defaults, '_ip_json', lambda *args: pytest.fail('Host network must not be inspected'))
    try:
        assert defaults.automatic_proxy_peers() == defaults.LOOPBACK
    finally:
        defaults.automatic_proxy_peers.cache_clear()

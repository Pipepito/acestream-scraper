"""Runs inside the built image: the guard against a real kernel, offline.

Two veth links stand in for the uplink and the WARP tunnel. Their peers never
answer, so an allowed connection times out and a blocked one is refused.
No packet leaves the container (`--network none`).
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, '/app')
import warp_guard  # noqa: E402  (the packaged copy is the subject)

PUBLIC, PUBLIC6, PRIVATE, THROUGH_TUNNEL = '192.0.2.10', '2001:db8::10', '10.20.30.40', '203.0.113.10'


def sh(command: str) -> None:
    subprocess.run(command.split(), check=True)


def attempt(address: str, group: int | None = None) -> str:
    """'refused' when the kernel rejects the connection locally, else 'sent'."""
    reader, writer = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(reader)
        if group is not None:
            os.setgroups([])
            os.setgid(group)
        family = socket.AF_INET6 if ':' in address else socket.AF_INET
        with socket.socket(family, socket.SOCK_STREAM) as connection:
            # Shorter than the kernel's own neighbour-discovery failure.
            connection.settimeout(2.5)
            try:
                connection.connect((address, 443))
                result = 'connected'
            except ConnectionRefusedError:
                # The guard's reject (or, on loopback, a closed port).
                result = 'refused'
            except OSError:
                result = 'sent'
        os.write(writer, result.encode())
        os._exit(0)
    os.close(writer)
    os.waitpid(pid, 0)
    with os.fdopen(reader) as stream:
        return stream.read()


def expect(label: str, actual, wanted) -> None:
    print(f'{label}: {actual}')
    if actual != wanted:
        sys.exit(f'FAILED {label}: expected {wanted!r}, got {actual!r}')


def table_present() -> bool:
    return subprocess.run(['nft', 'list', 'table', 'inet', warp_guard.TABLE], capture_output=True).returncode == 0


sh('ip link add uplink type veth peer name uplink-peer')
sh(f'ip link add {warp_guard.TUNNEL_INTERFACE} type veth peer name tunnel-peer')
for link in ('uplink', 'uplink-peer', warp_guard.TUNNEL_INTERFACE, 'tunnel-peer'):
    sh(f'ip link set {link} up')
sh('ip addr add 198.51.100.2/24 dev uplink')
sh('ip -6 addr add 2001:db8:1::2/64 dev uplink nodad')
sh(f'ip addr add 172.16.0.2/32 dev {warp_guard.TUNNEL_INTERFACE}')
sh('ip route add default dev uplink')
sh('ip -6 route add default dev uplink')
sh(f'ip route add 203.0.113.0/24 dev {warp_guard.TUNNEL_INTERFACE}')

rules = Path('/run/warp-guard-check.nft')
guard = warp_guard.Guard(rules)

expect('before the guard, public traffic leaves', attempt(PUBLIC), 'sent')
guard.install()
expect('armed: public IPv4 from the app', attempt(PUBLIC), 'refused')
expect('armed: public IPv6 from the app', attempt(PUBLIC6), 'refused')
expect('armed: the WARP daemon group', attempt(PUBLIC, warp_guard.GROUP_ID), 'sent')
expect('armed: another group', attempt(PUBLIC, warp_guard.GROUP_ID + 1), 'refused')
expect('armed: a private network', attempt(PRIVATE), 'sent')
expect('armed: through the tunnel interface', attempt(THROUGH_TUNNEL), 'sent')
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 443))
    listener.listen()
    expect('armed: loopback', attempt('127.0.0.1'), 'connected')
guard.arm()
expect('re-armed: still blocking', attempt(PUBLIC), 'refused')
guard.standby()
expect('standby: table removed', table_present(), False)
expect('standby: public traffic leaves', attempt(PUBLIC), 'sent')

# An unattended block must expire by itself.
warp_guard.HOLD_SECONDS = 2
guard.install()
expect('short hold: blocking', attempt(PUBLIC), 'refused')
time.sleep(3)
expect('short hold expired: public traffic leaves', attempt(PUBLIC), 'sent')
guard.standby()
print('WARP guard kernel check passed')

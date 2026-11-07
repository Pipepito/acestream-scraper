"""Bounded, non-blocking reader for an opt-in Gluetun shared port file.

Only returns a port, never file content or a path, to the engine supervisor.
No network, credentials, shell evaluation, or writes to Gluetun's volume.
"""
import os
import re
import stat
import sys


def read_port(path: str, reserved: set[int]) -> int | None:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > 32:
                return None
            raw = os.read(fd, 33)
        finally:
            os.close(fd)
    except OSError:
        return None
    if not re.fullmatch(rb"[ \t\r\n]*[0-9]{1,5}[ \t\r\n]*", raw):
        return None
    port = int(raw)
    return port if 1024 <= port <= 65535 and port not in reserved else None


def reserved_ports() -> set[int]:
    # Container listeners and the checker's independent P2P port must not be
    # displaced by a provider-assigned port. Include defaults conservatively.
    ports = {6879, 6880, 6881, 62062, 62063, 8622, 9050, 9051}
    for name, default in {
        "FLASK_PORT": 8000, "ACESTREAM_HTTP_PORT": 6878,
        "ACEXY_STATUS_PORT": 8080, "IPFS_SWARM_PORT": 4001,
        "IPFS_API_PORT": 5001, "IPFS_GATEWAY_PORT": 8081,
        "ZERONET_UI_PORT": 43110, "ZERONET_FILESERVER_PORT": 26552,
    }.items():
        try:
            ports.add(int(os.environ.get(name, str(default))))
        except ValueError:
            pass
    return ports


if __name__ == "__main__":
    value = read_port(os.environ["ACESTREAM_GLUETUN_PORT_FILE"], reserved_ports())
    if value is None:
        sys.exit(1)
    print(value)

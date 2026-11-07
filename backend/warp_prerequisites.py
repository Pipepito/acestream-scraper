"""Check the documented WARP container prerequisites without changing networking."""
import os
from pathlib import Path
import stat
import sys


WARP_DOCKER_GUIDANCE = (
    "WARP cannot start with this container's permissions. Recreate the container "
    "with --cap-add NET_ADMIN --device /dev/net/tun:/dev/net/tun, "
    "keeping your existing data mounts. Alternatively, disable WARP in the saved "
    "runtime-config.json and recreate the container. Network services are paused "
    "to prevent a direct-connection fallback."
)
WARP_SETUP_GUIDANCE = (
    "WARP setup did not complete. Network services are paused to prevent a "
    "direct-connection fallback. Download diagnostics, check the WARP logs, "
    "correct the configuration and restart the container."
)
WARP_DNS_GUIDANCE = (
    "WARP DNS-only mode needs --cap-add NET_ADMIN to configure container networking. "
    "Recreate the container with that capability, keeping your existing data mounts. "
    "DNS-only mode does not need SYS_ADMIN or /dev/net/tun. Network services are "
    "paused until the configuration is fixed and the container restarted."
)


class WarpStartupError(RuntimeError):
    """A startup failure with a fixed, credential-free operator message."""


def missing_prerequisites(status_path=Path('/proc/self/status'), tun_path=Path('/dev/net/tun'), *, dns_only=False):
    missing = []
    try:
        fields = dict(line.split(':', 1) for line in status_path.read_text().splitlines() if ':' in line)
        capabilities = int(fields['CapEff'].strip(), 16)
    except (OSError, KeyError, ValueError):
        capabilities = 0
    required = [('NET_ADMIN', 12)]
    for name, bit in required:
        if not capabilities & (1 << bit):
            missing.append(name)
    if dns_only:
        return missing
    try:
        metadata = tun_path.stat()
        if not stat.S_ISCHR(metadata.st_mode) or (os.major(metadata.st_rdev), os.minor(metadata.st_rdev)) != (10, 200):
            raise OSError('Not a TUN device')
        # A device node alone does not prove the container device policy allows it.
        descriptor = os.open(tun_path, os.O_RDWR | os.O_NONBLOCK)
        os.close(descriptor)
    except OSError:
        missing.append('/dev/net/tun (missing or inaccessible)')
    return missing


if __name__ == '__main__':
    dns_only = os.environ.get('WARP_DNS_ONLY', '').lower() in ('true', '1', 'yes', 'on')
    missing = missing_prerequisites(dns_only=dns_only)
    if missing:
        print('Missing WARP prerequisites: ' + ', '.join(missing), file=sys.stderr)
        print(WARP_DNS_GUIDANCE if dns_only else WARP_DOCKER_GUIDANCE, file=sys.stderr)
        sys.exit(78)

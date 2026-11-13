"""Block direct internet traffic while the WARP daemon is not in charge.

While warp-svc runs in automatic full-tunnel mode, Cloudflare's own firewall
rejects direct traffic, including during reconnects. That firewall disappears
when the daemon exits cleanly, and it does not exist before the first launch.
This guard covers exactly those periods with one private nftables table.

The daemon runs in its own group so its registration, DNS and tunnel traffic
pass without naming any Cloudflare address. The block expires unless it is
refreshed: a killed container cannot leave a host or shared network namespace
without internet access.

Stdlib only: used by the entrypoint, the startup coordinator and the app.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

TABLE = 'scraper_warp_guard'
# Inside the 65536 IDs a rootless container maps by default.
GROUP_ID = 5743
HOLD_SECONDS = 30
REFRESH_SECONDS = 5
TUNNEL_INTERFACE = 'CloudflareWARP'
# WARP's default exclusions: destinations it never tunnels.
LOCAL_IPV4 = ('10.0.0.0/8', '100.64.0.0/10', '169.254.0.0/16', '172.16.0.0/12', '192.0.0.0/24',
              '192.168.0.0/16', '224.0.0.0/24', '239.255.255.250', '255.255.255.255')
LOCAL_IPV6 = ('fc00::/7', 'fe80::/10', 'ff01::/16', 'ff02::/16', 'ff03::/16', 'ff04::/16', 'ff05::/16')
REMOVAL = f'add table inet {TABLE}\ndelete table inet {TABLE}\n'
TRUE = ('1', 'true', 'yes', 'on')


class GuardError(RuntimeError):
    """The guard could not be changed; the caller decides how to fail closed."""


def _flag(environ, name: str, default: str = 'false') -> bool:
    return str(environ.get(name, default)).strip().lower() in TRUE


def enabled(environ=os.environ) -> bool:
    """Only the mode whose startup already requires a connected tunnel."""
    return (_flag(environ, 'ENABLE_WARP') and _flag(environ, 'WARP_ENABLE_NAT')
            and not _flag(environ, 'WARP_DNS_ONLY') and _flag(environ, 'WARP_KILL_SWITCH', 'true'))


def armed_rules() -> str:
    return REMOVAL + f'''table inet {TABLE} {{
    set armed {{
        type nf_proto
        flags timeout
        elements = {{ ipv4 timeout {HOLD_SECONDS}s, ipv6 timeout {HOLD_SECONDS}s }}
    }}
    chain output {{
        type filter hook output priority 0; policy accept;
        meta nfproto != @armed accept
        oifname {{ "lo", "{TUNNEL_INTERFACE}" }} accept
        meta skgid {GROUP_ID} accept
        ip daddr {{ {', '.join(LOCAL_IPV4)} }} accept
        ip6 daddr {{ {', '.join(LOCAL_IPV6)} }} accept
        reject
    }}
}}
'''


def group_available() -> None:
    """Prove the daemon can enter its group before anything depends on it."""
    pid = os.fork()
    if pid == 0:
        try:
            os.setgroups([])
            os.setgid(GROUP_ID)
        except OSError:
            os._exit(1)
        os._exit(0)
    if os.waitpid(pid, 0)[1] != 0:
        raise GuardError('The container cannot change group; the default SETGID capability is required.')


class Guard:
    def __init__(self, rules: Path, *, run=subprocess.run):
        self.rules, self.run = Path(rules), run

    def _nft(self, source: str, text: str | None = None) -> None:
        try:
            result = self.run(['nft', '-f', source], input=text, capture_output=True,
                              text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise GuardError('nft is unavailable or did not answer.') from None
        if result.returncode:
            raise GuardError('nftables rejected the guard rules; the host kernel may lack support.')

    def arm(self) -> None:
        self._nft(str(self.rules))

    def standby(self) -> None:
        self._nft('-', REMOVAL)

    def active(self) -> bool:
        """Whether the kernel holds the block right now; never inferred."""
        try:
            result = self.run(['nft', '-j', 'list', 'set', 'inet', TABLE, 'armed'],
                              capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise GuardError('nft is unavailable or did not answer.') from None
        if result.returncode:
            if 'No such file or directory' in result.stderr:
                return False
            raise GuardError('nftables could not report the guard state.')
        try:
            held = {entry['elem']['val'] for item in json.loads(result.stdout)['nftables']
                    if 'set' in item for entry in item['set'].get('elem', [])}
        except (ValueError, KeyError, TypeError):
            raise GuardError('nftables returned an unsupported guard state.') from None
        # An expired hold leaves the table in place, passing everything.
        return {'ipv4', 'ipv6'} <= held

    def install(self, *, check_group=group_available) -> None:
        check_group()
        if self.rules.is_symlink():
            raise GuardError('The guard rules must be a regular file.')
        try:
            fd, temporary = tempfile.mkstemp(prefix='.warp-guard-', dir=self.rules.parent)
            try:
                with os.fdopen(fd, 'w') as stream:
                    stream.write(armed_rules())
                os.replace(temporary, self.rules)
            finally:
                Path(temporary).unlink(missing_ok=True)
        except OSError:
            raise GuardError('The guard rules could not be written.') from None
        self.arm()


def run_daemon(command: str) -> None:
    os.setgroups([])
    os.setgid(GROUP_ID)
    os.execvp('bash', ['bash', '-lc', command])


def main(argv: list[str]) -> int:
    action = argv[1] if len(argv) > 1 else ''
    if action == 'enabled':
        return 0 if enabled() else 1
    try:
        if action == 'daemon' and len(argv) == 3:
            run_daemon(argv[2])
        elif action in ('install', 'arm') and len(argv) == 3:
            getattr(Guard(Path(argv[2])), action)()
        elif action == 'standby' and len(argv) == 2:
            Guard(Path(os.devnull)).standby()
        else:
            raise GuardError('Unknown guard action.')
    except (GuardError, OSError) as exc:
        detail = str(exc) if isinstance(exc, GuardError) else 'The daemon group could not be entered.'
        print(f'WARP traffic guard unavailable: {detail}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

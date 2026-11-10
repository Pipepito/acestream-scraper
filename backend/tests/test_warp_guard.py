"""The WARP traffic guard: rules, activation and the daemon's exempt group."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

import warp_guard
from warp_guard import Guard, GuardError


FULL_TUNNEL = {'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true'}


@pytest.mark.parametrize('environment, expected', [
    (FULL_TUNNEL, True),
    ({**FULL_TUNNEL, 'WARP_KILL_SWITCH': 'true'}, True),
    ({**FULL_TUNNEL, 'WARP_KILL_SWITCH': 'false'}, False),
    # Manual connection and DNS-only mode keep the normal connection by design.
    ({'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'false'}, False),
    ({**FULL_TUNNEL, 'WARP_DNS_ONLY': 'true'}, False),
    ({'ENABLE_WARP': 'false', 'WARP_ENABLE_NAT': 'true'}, False),
    ({}, False),
])
def test_guard_applies_only_to_automatic_full_tunnel(environment, expected):
    assert warp_guard.enabled(environment) is expected


def test_armed_rules_replace_the_table_atomically_and_expire_unattended():
    rules = warp_guard.armed_rules()
    lines = [line.strip() for line in rules.splitlines() if line.strip()]
    # One transaction: an existing table is replaced, never merged with.
    assert lines[:2] == ['add table inet scraper_warp_guard', 'delete table inet scraper_warp_guard']
    # The block holds only while it is refreshed, so a killed container cannot
    # leave a host or shared network namespace without internet access.
    assert f'ipv4 timeout {warp_guard.HOLD_SECONDS}s' in rules
    assert f'ipv6 timeout {warp_guard.HOLD_SECONDS}s' in rules
    assert 'meta nfproto != @armed accept' in rules
    assert warp_guard.HOLD_SECONDS > warp_guard.REFRESH_SECONDS * 3


def test_armed_rules_pass_only_loopback_tunnel_daemon_and_local_networks():
    rules = warp_guard.armed_rules()
    body = rules[rules.index('chain output'):]
    verdicts = [line.strip() for line in body.splitlines() if line.strip().endswith(('accept', 'reject'))]
    assert verdicts[-1] == 'reject'
    assert verdicts.count('reject') == 1
    assert 'oifname { "lo", "CloudflareWARP" } accept' in verdicts
    assert f'meta skgid {warp_guard.GROUP_ID} accept' in verdicts
    assert 'type filter hook output priority 0; policy accept;' in body
    for network in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '100.64.0.0/10', '169.254.0.0/16', 'fc00::/7', 'fe80::/10'):
        assert network in body
    # Nothing public is exempt: no default route, no resolver, no Cloudflare range.
    for public in ('0.0.0.0/0', '::/0', '1.1.1.1', '8.8.8.8', '162.159.'):
        assert public not in body


def test_arm_and_standby_feed_nft_without_a_shell(tmp_path):
    calls = []

    def run(argv, **options):
        calls.append((argv, options.get('input')))
        return subprocess.CompletedProcess(argv, 0, '', '')

    rules = tmp_path / 'warp-guard.nft'
    rules.write_text(warp_guard.armed_rules())
    guard = Guard(rules, run=run)
    guard.arm()
    guard.standby()
    assert calls[0] == (['nft', '-f', str(rules)], None)
    assert calls[1][0] == ['nft', '-f', '-']
    assert calls[1][1].split() == ['add', 'table', 'inet', 'scraper_warp_guard',
                                  'delete', 'table', 'inet', 'scraper_warp_guard']


@pytest.mark.parametrize('failure', [
    subprocess.CompletedProcess(['nft'], 1, '', 'Error: Could not process rule'),
    FileNotFoundError('nft'),
    subprocess.TimeoutExpired(['nft'], 10),
])
def test_nft_failures_are_reported_never_ignored(tmp_path, failure):
    def run(argv, **options):
        if isinstance(failure, BaseException):
            raise failure
        return failure

    guard = Guard(tmp_path / 'warp-guard.nft', run=run)
    with pytest.raises(GuardError):
        guard.arm()
    with pytest.raises(GuardError):
        guard.standby()


def test_install_writes_private_rules_then_arms(tmp_path):
    calls = []
    rules = tmp_path / 'warp-guard.nft'

    def run(argv, **options):
        calls.append(argv)
        assert rules.read_text() == warp_guard.armed_rules()
        return subprocess.CompletedProcess(argv, 0, '', '')

    Guard(rules, run=run).install(check_group=lambda: None)
    assert calls == [['nft', '-f', str(rules)]]
    assert rules.stat().st_mode & 0o077 == 0


def test_install_refuses_when_the_daemon_group_is_unavailable(tmp_path):
    def refused():
        raise GuardError('The container cannot change group.')

    rules = tmp_path / 'warp-guard.nft'
    with pytest.raises(GuardError):
        Guard(rules, run=lambda *a, **k: pytest.fail('nft must not run')).install(check_group=refused)
    assert not rules.exists()


def test_install_never_writes_through_a_symlink(tmp_path):
    target = tmp_path / 'elsewhere'
    target.write_text('keep')
    rules = tmp_path / 'warp-guard.nft'
    rules.symlink_to(target)
    with pytest.raises(GuardError):
        Guard(rules, run=lambda *a, **k: subprocess.CompletedProcess(a, 0, '', '')).install(check_group=lambda: None)
    assert target.read_text() == 'keep'


def test_daemon_command_runs_in_the_exempt_group(tmp_path, monkeypatch):
    """Only a privileged process may change group; record what is requested."""
    steps = []
    monkeypatch.setattr(os, 'setgroups', lambda groups: steps.append(('groups', groups)))
    monkeypatch.setattr(os, 'setgid', lambda gid: steps.append(('gid', gid)))
    monkeypatch.setattr(os, 'execvp', lambda program, argv: steps.append((program, argv)))
    warp_guard.run_daemon('warp-svc --accept-tos')
    assert steps == [('groups', []), ('gid', warp_guard.GROUP_ID),
                     ('bash', ['bash', '-lc', 'warp-svc --accept-tos'])]


def test_command_line_reports_whether_the_guard_applies():
    script = Path(warp_guard.__file__)
    environment = {**os.environ, **FULL_TUNNEL}
    environment.pop('WARP_KILL_SWITCH', None)
    environment.pop('WARP_DNS_ONLY', None)
    assert subprocess.run([sys.executable, str(script), 'enabled'], env=environment).returncode == 0
    assert subprocess.run([sys.executable, str(script), 'enabled'],
                          env={**environment, 'WARP_KILL_SWITCH': 'false'}).returncode == 1


def test_command_line_failures_exit_nonzero_with_a_fixed_message(tmp_path):
    script = Path(warp_guard.__file__)
    environment = {**os.environ, 'PATH': str(tmp_path)}  # no nft here
    result = subprocess.run([sys.executable, str(script), 'arm', str(tmp_path / 'missing.nft')],
                            env=environment, capture_output=True, text=True)
    assert result.returncode == 1
    assert 'WARP traffic guard' in result.stderr


@pytest.mark.parametrize('stdout, expected', [
    ('{"nftables": [{"metainfo": {}}, {"set": {"name": "armed", "elem": [{"elem": {"val": "ipv4", "timeout": 30, "expires": 12}}, {"elem": {"val": "ipv6", "timeout": 30, "expires": 12}}]}}]}', True),
    # Expired: the table remains but passes everything.
    ('{"nftables": [{"metainfo": {}}, {"set": {"name": "armed"}}]}', False),
    ('{"nftables": [{"set": {"name": "armed", "elem": [{"elem": {"val": "ipv4", "timeout": 30, "expires": 3}}]}}]}', False),
])
def test_active_reads_whether_the_block_is_held_right_now(tmp_path, stdout, expected):
    def run(argv, **options):
        assert argv == ['nft', '-j', 'list', 'set', 'inet', 'scraper_warp_guard', 'armed']
        return subprocess.CompletedProcess(argv, 0, stdout, '')

    assert Guard(tmp_path / 'rules', run=run).active() is expected


def test_active_is_false_without_the_table_and_an_error_when_nft_cannot_tell(tmp_path):
    missing = subprocess.CompletedProcess(['nft'], 1, '', 'Error: No such file or directory')
    assert Guard(tmp_path / 'rules', run=lambda *a, **k: missing).active() is False
    garbage = subprocess.CompletedProcess(['nft'], 0, 'not json', '')
    with pytest.raises(GuardError):
        Guard(tmp_path / 'rules', run=lambda *a, **k: garbage).active()

    def unavailable(*a, **k):
        raise FileNotFoundError('nft')

    with pytest.raises(GuardError):
        Guard(tmp_path / 'rules', run=unavailable).active()

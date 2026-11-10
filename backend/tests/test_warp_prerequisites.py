"""WARP failures keep diagnostics reachable without starting network workloads."""
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

import pytest

import warp_prerequisites as prerequisites


@pytest.mark.parametrize('missing', ['NET_ADMIN', None])
def test_checks_net_admin_and_device_access_without_requiring_sys_admin(tmp_path, monkeypatch, missing):
    status = tmp_path / 'status'
    bits = {'NET_ADMIN': 12}
    status.write_text(f"CapEff:\t{sum(1 << bit for name, bit in bits.items() if name != missing):x}\n")
    device = SimpleNamespace(stat=lambda: SimpleNamespace(st_mode=stat.S_IFCHR, st_rdev=os.makedev(10, 200)))
    opened = []
    monkeypatch.setattr(prerequisites.os, 'open', lambda *args: opened.append(args) or 99)
    monkeypatch.setattr(prerequisites.os, 'close', lambda fd: None)
    assert prerequisites.missing_prerequisites(status, device) == ([missing] if missing else [])
    assert opened


def test_regular_file_is_not_a_tun_device(tmp_path):
    status = tmp_path / 'status'
    status.write_text('CapEff: 201000\n')
    device = tmp_path / 'tun'
    device.touch()
    assert prerequisites.missing_prerequisites(status, device) == ['/dev/net/tun (missing or inaccessible)']


def test_inaccessible_device_is_reported(tmp_path, monkeypatch):
    status = tmp_path / 'status'
    status.write_text('CapEff: 201000\n')
    device = SimpleNamespace(stat=lambda: SimpleNamespace(st_mode=stat.S_IFCHR, st_rdev=os.makedev(10, 200)))
    def denied(*args):
        raise PermissionError
    monkeypatch.setattr(prerequisites.os, 'open', denied)
    # The node is mapped, so "missing" would send the operator the wrong way.
    assert prerequisites.missing_prerequisites(status, device) == ['/dev/net/tun (present, but access is denied)']


@pytest.mark.parametrize('capabilities,expected', [('1000', []), ('200000', ['NET_ADMIN']), ('0', ['NET_ADMIN'])])
def test_dns_only_needs_net_admin_but_never_opens_tun(tmp_path, capabilities, expected):
    status = tmp_path / 'status'
    status.write_text(f'CapEff: {capabilities}\n')
    assert prerequisites.missing_prerequisites(status, tmp_path / 'missing-device', dns_only=True) == expected


@pytest.mark.parametrize('auto_connect', ['true', 'false'])
def test_entrypoint_keeps_app_but_never_starts_sidecars_after_warp_failure(tmp_path, auto_connect):
    root = Path(__file__).resolve().parents[2]
    marker = tmp_path / 'sidecar-started'
    env = {**os.environ, 'SCRAPER_RUNTIME_LOADED': '1',
           'LOG_DIR': str(tmp_path / 'logs'), 'LOGROTATE_DIR': str(tmp_path / 'rotate'),
           'SUPERVISOR_RUN_DIR': str(tmp_path / 'run'),
           'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': auto_connect,
           'WARP_REQUIRED_COMMANDS': 'deliberately-missing-warp-binary',
           'ENABLE_ACESTREAM_ENGINE': 'true', 'IMAGE_HAS_ACESTREAM': 'true',
           'ENABLE_ACESTREAM_CHECK_ENGINE': 'true',
           'ENABLE_ACEXY': 'true', 'IMAGE_HAS_ACEXY': 'true',
           'ENABLE_ZERONET': 'true', 'IMAGE_HAS_ZERONET': 'true',
           'ENABLE_IPFS': 'true', 'IMAGE_HAS_IPFS': 'true', 'ENABLE_TOR': 'true'}
    for name in ['ACESTREAM', 'ACEXY', 'ZERONET', 'IPFS']:
        env[name + '_START_COMMAND'] = f'touch "{marker}"'
    result = subprocess.run(['bash', str(root / 'entrypoint.sh'), 'bash', '-c',
                             'test "$SCRAPER_WARP_STARTUP_ERROR" = setup && echo APP_AVAILABLE'],
                            env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'APP_AVAILABLE' in result.stdout
    assert not marker.exists()

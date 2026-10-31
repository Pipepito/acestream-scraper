"""Run inside the built production image; no source overlays or network needed."""
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=60, **kwargs).stdout


# Build-only packaging tools must actually be absent, including bootstrap wheels.
for executable in [Path('/usr/local/bin/python3'), Path('/usr/local/bin/python3.10'),
                   Path('/opt/zeronet/python/bin/python3.11')]:
    if executable.exists():
        run(str(executable), '-c',
            'import importlib.util; assert all(importlib.util.find_spec(n) is None '
            'for n in ("pip", "ensurepip", "setuptools", "wheel"))',
            env=dict(os.environ, LD_LIBRARY_PATH='/opt/zeronet/python/lib:/usr/local/lib'))

ipfs = Path('/opt/ipfs/bin/ipfs')
if ipfs.exists():
    with tempfile.TemporaryDirectory(prefix='security-ipfs-') as temp:
        env = dict(os.environ, IPFS_PATH=temp + '/repo')
        run(str(ipfs), 'init', '--profile=test', env=env)
        content = Path(temp) / 'owned.txt'
        content.write_text('Owned offline IPFS security regression fixture.\n')
        cid = run(str(ipfs), 'add', '-Q', str(content), env=env).strip()
        assert run(str(ipfs), 'cat', cid, env=env) == content.read_text()
        # Restart the same repository and exercise the daemon's real HTTP API.
        run(str(ipfs), 'config', 'Addresses.API', '/ip4/127.0.0.1/tcp/15001', env=env)
        log = open(Path(temp) / 'daemon.log', 'w+')
        daemon = subprocess.Popen([str(ipfs), 'daemon', '--offline', '--migrate=false'],
                                  env=env, stdout=log, stderr=log)
        try:
            for attempt in range(60):
                assert daemon.poll() is None, 'IPFS daemon exited before readiness'
                try:
                    with urlopen(Request('http://127.0.0.1:15001/api/v0/cat?arg=' + cid,
                                         data=b''), timeout=1) as response:
                        assert response.read().decode() == content.read_text()
                    break
                except OSError:
                    time.sleep(0.25)
            else:
                raise AssertionError('IPFS API did not become ready')
        finally:
            daemon.terminate()
            try:
                daemon.wait(timeout=15)
            except subprocess.TimeoutExpired:
                daemon.kill()
                daemon.wait(timeout=5)
            log.close()

if Path('/opt/zeronet/bin/zeronet').exists():
    assert '--ui-port' in run('/opt/zeronet/bin/zeronet', '--no-bootstrap', '--help')

if Path('/usr/bin/warp-cli').exists():
    assert 'warp-cli' in run('/usr/bin/warp-cli', '--version').lower()
    for tool in ('warp-cli', 'warp-svc', 'warp-dex', 'warp-diag'):
        assert 'not found' not in run('ldd', '/usr/bin/' + tool)
    assert not Path('/usr/lib/warp/warp-taskbar').exists()
    packages = run('dpkg-query', '-W', '-f=${Package}\n').splitlines()
    assert not any(name.startswith(('libsoup', 'libwebkit', 'libjavascriptcore')) for name in packages)
    assert Path('/usr/share/doc/cloudflare-warp/package-control').is_file()

print('Security dependency runtime smoke passed')

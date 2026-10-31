"""Runtime compatibility for the security dependency and headless package changes."""
import os
from pathlib import Path
import platform
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[3]


def test_security_dependencies_in_production_image():
    image = os.environ.get('SECURITY_TEST_IMAGE')
    owned = image is None
    if owned:
        image = 'acestream-security-smoke:' + uuid.uuid4().hex[:12]
    try:
        if owned:
            target = 'linux/arm64' if platform.machine() in ('arm64', 'aarch64') else 'linux/amd64'
            subprocess.run(['bash', str(ROOT / 'scripts/ci/build_multiarch_images.sh'),
                            '--flavor', 'scraper-acestream-acexy', '--platforms', target,
                            '--load', '--tag', image], cwd=ROOT, check=True)
        probe = (ROOT / 'docker/testdata/security_dependency_smoke.py').read_text()
        subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--cap-drop', 'ALL',
                        '--security-opt', 'no-new-privileges', '--entrypoint', 'python',
                        image, '-'], input=probe, text=True, check=True, timeout=180)
    finally:
        if owned:
            subprocess.run(['docker', 'image', 'rm', image], check=False, capture_output=True)

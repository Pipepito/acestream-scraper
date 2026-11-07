"""Legacy install entry points must not resurrect the retired Flask runtime."""
from pathlib import Path

import pytest


@pytest.mark.parametrize('name', ['requirements.txt', 'requirements-dev.txt', 'requirements-prod.txt'])
def test_root_requirements_delegate_to_canonical_backend(name):
    root = Path(__file__).resolve().parents[2]
    requirements = [line.strip() for line in (root / name).read_text().splitlines()
                    if line.strip() and not line.startswith('#')]
    assert requirements == ['-r backend/requirements.txt']

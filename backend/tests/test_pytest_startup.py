"""Exercise plugin startup independently of the application's fixture harness."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("emit_warning", [False, True])
def test_asyncio_startup_preserves_fixture_scope_and_warning_errors(tmp_path, emit_warning):
    probe = tmp_path / "test_probe.py"
    probe.write_text(
        """import asyncio
import warnings
import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def fixture_loop():
    yield asyncio.get_running_loop()

@pytest.mark.asyncio
@pytest.mark.parametrize("case", [1, 2])
async def test_loop(fixture_loop, pytestconfig, case):
    assert pytestconfig.getini("asyncio_default_fixture_loop_scope") == "function"
    assert fixture_loop is asyncio.get_running_loop()
"""
        + ("    warnings.warn('startup regression probe', DeprecationWarning)\n" if emit_warning else ""),
        encoding="utf-8",
    )
    env = os.environ.copy()
    # Load the required plugin explicitly so unrelated installed plugins cannot
    # hide a startup/configuration regression. Keep the real warnings policy.
    for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONWARNINGS"):
        env.pop(key, None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-c",
         str(Path(__file__).resolve().parents[1] / "pytest.ini"),
         "--noconftest", "-p", "pytest_asyncio.plugin", "-q", str(probe)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode == (1 if emit_warning else 0), output
    assert "INTERNALERROR" not in output
    assert ("2 failed" if emit_warning else "2 passed") in output
    if emit_warning:
        assert "DeprecationWarning: startup regression probe" in output

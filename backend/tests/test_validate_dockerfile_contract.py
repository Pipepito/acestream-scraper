import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts/ci/validate_dockerfile_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_dockerfile_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
runtime_command_errors = MODULE.runtime_command_errors


def test_runtime_command_delegates_to_entrypoint():
    assert runtime_command_errors(['CMD []']) == []


def test_runtime_command_rejects_hardcoded_uvicorn_port():
    runtime = [
        'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", '
        '"--no-proxy-headers", "--timeout-graceful-shutdown", "3"]'
    ]

    assert runtime_command_errors(runtime) == [
        "runtime-base CMD must be empty so entrypoint.sh honors FLASK_PORT"
    ]


@pytest.mark.parametrize("runtime", [
    [],
    ['CMD []', 'CMD []'],
    ['CMD uvicorn main:app'],
    ['CMD ""'],
    ['CMD [0]'],
])
def test_runtime_command_requires_one_explicit_empty_json_command(runtime):
    assert runtime_command_errors(runtime)

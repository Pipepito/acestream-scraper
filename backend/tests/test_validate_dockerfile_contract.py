import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts/ci/validate_dockerfile_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_dockerfile_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
runtime_command_errors = MODULE.runtime_command_errors


def test_runtime_command_accepts_additional_uvicorn_flags():
    runtime = [
        'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", '
        '"--no-proxy-headers", "--timeout-graceful-shutdown", "3"]'
    ]

    assert runtime_command_errors(runtime) == []


def test_runtime_command_rejects_an_incorrect_bind_address():
    runtime = ['CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]']

    assert runtime_command_errors(runtime) == [
        "runtime-base CMD must set --host to 0.0.0.0"
    ]

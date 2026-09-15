"""Run the production ARM bootstrap with synthetic engine entry points.

Version/health checks cannot detect starting the OCI payload through the wrong
entry point. These offline tests verify distribution selection and the existing
configuration/error contract without requiring proprietary binaries or streams.
"""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time

import pytest

BOOTSTRAP = Path(__file__).resolve().parents[2] / "docker/scripts/acestream-android/main_linux.py"


@pytest.fixture
def engine(tmp_path):
    shutil.copy(BOOTSTRAP, tmp_path / "main_linux.py")
    home = tmp_path / "state"
    home.mkdir()
    (home / "acestream.conf").write_text("--http-port\n6880\n")
    (tmp_path / "app_bridge.py").write_text(
        "import os\nclass Android:\n"
        "    def getAceStreamHome(self): return os.environ['ACESTREAM_HOME']\n"
    )
    recorder = (
        "import json, os, sys\nfrom pathlib import Path\n"
        "def record(entry, args):\n"
        "    Path(os.environ['RESULT']).write_text(json.dumps({'entry':entry,'args':args}))\n"
    )
    (tmp_path / "record.py").write_text(recorder)
    (tmp_path / "aceserve.py").write_text(
        "from record import record\nimport sys\n"
        "def main(): record('aceserve', sys.argv)\n"
    )
    (tmp_path / "acestreamengine.py").write_text(
        "from record import record\nclass Core:\n"
        "    @staticmethod\n    def run(args): record('Core', args)\n"
    )
    # Avoid importing host DNS dependencies; these tests never resolve hosts.
    (tmp_path / "dns.py").write_text("raise ImportError('offline fixture')\n")
    return tmp_path


def run_engine(engine):
    return subprocess.run(
        [sys.executable, str(engine / "main_linux.py"), "--http-port", "6878", "--log-stdout"],
        env={**os.environ, "ACESTREAM_HOME": str(engine / "state"),
             "RESULT": str(engine / "result.json")},
        capture_output=True, text=True, timeout=10,
    )


@pytest.mark.parametrize("oci,expected", [(True, "aceserve"), (False, "Core")])
def test_distribution_entrypoint_preserves_launch_and_config_arguments(engine, oci, expected):
    if oci:
        (engine / "main.py.oci-orig").write_text("upstream bootstrap retained by installer\n")
    result = run_engine(engine)
    assert result.returncode == 0, result.stderr
    recorded = json.loads((engine / "result.json").read_text())
    assert recorded["entry"] == expected
    assert recorded["args"][1:] == [
        "--http-port", "6878", "--log-stdout", "--client-console", "--http-port", "6880",
    ]
    assert (engine / "state/acestream.log").is_file()


@pytest.mark.parametrize("failure", ["missing", "runtime"])
def test_broken_oci_entrypoint_exits_instead_of_falling_back_to_core(engine, failure):
    (engine / "main.py.oci-orig").touch()
    if failure == "missing":
        (engine / "aceserve.py").unlink()
    else:
        (engine / "aceserve.py").write_text("def main(): raise RuntimeError('startup failed')\n")
    result = run_engine(engine)
    assert result.returncode == 1
    assert not (engine / "result.json").exists()
    assert "Traceback" in result.stderr
    assert "Traceback" in (engine / "state/acestream_error.log").read_text()


def test_engines_share_dns_socket_and_survivor_takes_over_after_owner_exits(tmp_path, request):
    shutil.copy(BOOTSTRAP.with_name("bionic_dns.py"), tmp_path / "bionic_dns.py")
    worker = tmp_path / "dns_worker.py"
    worker.write_text(
        "import os, socket, sys\nfrom bionic_dns import run_shared_listener\n"
        "path = sys.argv[1]\n"
        "def listener(resolver):\n"
        "    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:\n"
        "        server.bind(path)\n        server.listen(4)\n"
        "        while True:\n"
        "            client, _ = server.accept()\n"
        "            with client: client.sendall(str(os.getpid()).encode())\n"
        "run_shared_listener(listener, None, path)\n"
    )
    # Darwin AF_UNIX paths are limited to 104 bytes; pytest roots can exceed it.
    short_dir = tempfile.TemporaryDirectory(prefix="bionic-dns-", dir="/tmp")
    request.addfinalizer(short_dir.cleanup)
    path = str(Path(short_dir.name) / "dns.sock")

    def answer():
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(0.2)
            client.connect(path)
            return int(client.recv(32))

    def await_answer(expected):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                actual = answer()
                if actual in expected:
                    return actual
            except (OSError, ValueError):
                pass
            time.sleep(0.02)
        pytest.fail("surviving engine did not provide the shared DNS socket")

    processes = [subprocess.Popen([sys.executable, str(worker), path]) for _ in range(2)]
    try:
        owner = await_answer({p.pid for p in processes})
        # A concurrent engine must not unlink the existing listener's socket.
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            assert answer() == owner
            time.sleep(0.02)
        original = next(p for p in processes if p.pid == owner)
        survivor = next(p for p in processes if p.pid != owner)
        original.terminate()
        original.wait(timeout=5)
        assert await_answer({survivor.pid}) == survivor.pid
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)

"""Offline regressions against pinned upstream methods and the installer patch."""
from __future__ import annotations

import ast
import copy
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/zeronet/ContentManager.py.txt"
INSTALLER = ROOT / "docker/scripts/install-zeronet.sh"
PIN = "81d3ffc6bdfb600e9a1d4a091f1ceb131d92c4f1"


class VerifyError(Exception):
    pass


def apply_patch(path):
    patch = INSTALLER.read_text().split("<<'INNER_PATH_PATCH'\n", 1)[1].split(
        "\nINNER_PATH_PATCH", 1
    )[0]
    return subprocess.run(
        [sys.executable, "-", str(path)], input=patch, text=True, capture_output=True
    )


@pytest.fixture
def patched_source(tmp_path):
    path = tmp_path / "ContentManager.py"
    path.write_text(FIXTURE.read_text())
    result = apply_patch(path)
    assert result.returncode == 0, result.stderr
    return path.read_text()


def make_manager(source):
    crypt = Mock()
    crypt.verify.return_value = True
    namespace = {
        "Path": Path, "json": json, "re": re, "time": time,
        "VerifyError": VerifyError, "CryptBitcoin": crypt,
        "config": SimpleNamespace(fix_float_decimals=False),
        "Debug": SimpleNamespace(formatException=str),
        "SafeRe": re,
    }
    exec(compile(source, str(FIXTURE), "exec"), namespace)
    manager = namespace["ContentManager"]()
    manager.contents = {}
    manager.site = SimpleNamespace(
        address="site-owner", settings={"size": 123, "size_optional": 0},
        getSizeLimit=lambda: 1,
        worker_manager=SimpleNamespace(
            tasks=SimpleNamespace(findTask=Mock(return_value=None)), failTask=Mock()
        ),
    )
    manager.isArchived = Mock(return_value=False)
    manager.log = Mock()
    return manager, crypt


def manifest(**changes):
    return {
        "files": {}, "inner_path": "content.json", "address": "site-owner",
        "modified": 1, **changes,
    }


def test_fixture_matches_installer_pin():
    assert f"ZERONET_COMMIT:-{PIN}" in INSTALLER.read_text()


def test_patch_is_idempotent_and_supports_original_pr(tmp_path):
    source = FIXTURE.read_text()
    for before in (source, source.replace(
        "Path(content['inner_path']) != inner_path:",
        "Path(content['inner_path']) != Path(inner_path):",
    )):
        path = tmp_path / "ContentManager.py"
        path.write_text(before)
        assert apply_patch(path).returncode == 0
        once = path.read_text()
        ast.parse(once)
        assert apply_patch(path).returncode == 0
        assert path.read_text() == once
        # No changes outside verifyContent (especially signature verification).
        original = ast.parse(before).body[0]
        patched = ast.parse(once).body[0]
        for old, new in zip(original.body, patched.body):
            if old.name != "verifyContent":
                assert ast.dump(old) == ast.dump(new)


@pytest.mark.parametrize("replacement", ["False", "Path('unexpected.json')"])
def test_upstream_drift_fails_without_partial_write(tmp_path, replacement):
    path = tmp_path / "ContentManager.py"
    source = FIXTURE.read_text().replace(
        "if inner_path == Path('content.json'):", f"if inner_path == {replacement}:",
    )
    path.write_text(source)
    result = apply_patch(path)
    assert result.returncode != 0
    assert "recheck upstream pin" in result.stderr
    assert path.read_text() == source


def test_original_bug_and_patched_root_accounting(patched_source):
    original, _ = make_manager(FIXTURE.read_text())
    with pytest.raises(VerifyError, match="Wrong inner_path"):
        original.verifyContent("content.json", manifest())
    manager, _ = make_manager(patched_source)
    manager.verifyContentInclude = Mock(side_effect=AssertionError("root is not an include"))
    content = manifest(files={"index.html": {"size": 42}})
    assert manager.verifyContent("content.json", content) is True
    assert manager.site.settings["size"] == len(json.dumps(content, indent=1)) + 42
    manager.verifyContentInclude.assert_not_called()


@pytest.mark.parametrize("changes, error", [
    ({"inner_path": "data/content.json"}, "Wrong inner_path"),
    ({"address": "other-site"}, "Wrong site address"),
    ({"files": {"../outside": {"size": 1}}}, "Invalid relative path"),
])
def test_invalid_manifest_stays_rejected(patched_source, changes, error):
    manager, _ = make_manager(patched_source)
    with pytest.raises(VerifyError, match=error):
        manager.verifyContent("content.json", manifest(**changes))


def test_root_size_limit_aborts_download(patched_source):
    manager, _ = make_manager(patched_source)
    task = object()
    manager.site.worker_manager.tasks.findTask.return_value = task
    with pytest.raises(VerifyError, match="Content too large"):
        manager.verifyContent("content.json", manifest(description="x" * 1024 * 1024))
    manager.site.worker_manager.tasks.findTask.assert_called_once_with("content.json")
    manager.site.worker_manager.failTask.assert_called_once_with(task)


@pytest.mark.parametrize("accepted", [True, False])
def test_signature_verdict_is_enforced(patched_source, accepted):
    manager, crypt = make_manager(patched_source)
    crypt.verify.return_value = accepted
    signed = manifest(signs={"site-owner": "test-signature"})
    if accepted:
        assert manager.verifyFile("content.json", copy.deepcopy(signed)) is True
    else:
        with pytest.raises(VerifyError, match="Valid signs: 0/1"):
            manager.verifyFile("content.json", copy.deepcopy(signed))
    crypt.verify.assert_called_once()


def test_unsigned_manifest_is_rejected(patched_source):
    manager, crypt = make_manager(patched_source)
    with pytest.raises(VerifyError, match="Not signed"):
        manager.verifyFile("content.json", manifest())
    crypt.verify.assert_not_called()


def test_nested_manifest_still_requires_include_rules(patched_source):
    manager, _ = make_manager(patched_source)
    manager.getRules = Mock(return_value={"max_size": 0})
    with pytest.raises(VerifyError, match="Include too large"):
        manager.verifyContent("data/content.json", manifest(inner_path="data/content.json"))
    manager.getRules.assert_called_once()

"""The ARM engine docs must keep saying what playback a user can expect.

Both ARM platforms now use the matching variant of the community
`jopsis/acestream` 3.2.17 distribution. ARM64 API/startup is verified but live
playback is not; ARMv7 builds and installs but has not run on real hardware.
The docs must preserve that distinction and name `ACESTREAM_BIND_ALL`, which
reaches every platform through the entrypoint.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ARM_ENGINE_DOCS = ("docs/ops/acestream-arm-engine.md", "wiki/Docker.md")


@pytest.mark.parametrize("rel_path", ARM_ENGINE_DOCS)
def test_arm_engine_docs_describe_unverified_playback(rel_path: str):
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    lower = text.lower()
    assert "jopsis/acestream:v3.2.17-fix" in text
    assert "armv7" in lower and "runtime-tested" in lower
    assert "playback" in lower and ("unconfirmed" in lower or "unverified" in lower)


@pytest.mark.parametrize("rel_path", ARM_ENGINE_DOCS)
def test_arm_engine_docs_name_the_bind_all_knob(rel_path: str):
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    assert "ACESTREAM_BIND_ALL" in text, f"{rel_path} must document ACESTREAM_BIND_ALL"

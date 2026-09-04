"""The ARM engine docs must keep saying what playback a user can expect.

The 2026-09-03 spike established that the *official* Android engine is
premium-gated on every version: headless it answers "To continue, you need to
activate premium", and no engine bump lifts that. ARM64 escapes it only because
the image ships the community `jopsis/acestream` 3.2.17 distribution; ARMv7
still runs the official APK and therefore cannot play streams without a Premium
account. Both the operator guide and the user-facing Docker guide have to carry
that sentence, and both have to name `ACESTREAM_BIND_ALL`, which reaches every
platform through the entrypoint.

Deliberately assertions over prose, not over code: this is the one thing about
ARM playback a reader must not be able to lose in an edit.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ARM_ENGINE_DOCS = ("docs/ops/acestream-arm-engine.md", "wiki/Docker.md")


@pytest.mark.parametrize("rel_path", ARM_ENGINE_DOCS)
def test_arm_engine_docs_quote_the_premium_denial(rel_path: str):
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    assert "activate premium" in text.lower(), (
        f"{rel_path} must quote the engine's premium denial ('activate premium') so ARMv7 users "
        "know live playback needs a Premium account"
    )


@pytest.mark.parametrize("rel_path", ARM_ENGINE_DOCS)
def test_arm_engine_docs_name_the_bind_all_knob(rel_path: str):
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    assert "ACESTREAM_BIND_ALL" in text, f"{rel_path} must document ACESTREAM_BIND_ALL"

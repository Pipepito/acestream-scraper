#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh"
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "ci" / "verify_multiarch_manifest.sh"
PLATFORM_MANIFEST = REPO_ROOT / "docker" / "manifests" / "platforms.json"
ACESTREAM_MANIFEST = REPO_ROOT / "docker" / "manifests" / "acestream.json"


def acestream_platforms() -> list[str]:
    """Baseline platforms that have an AceStream engine (same rule as flavor_platforms.py)."""
    baseline = json.loads(PLATFORM_MANIFEST.read_text(encoding="utf-8"))["baseline_platforms"]
    supported = set(json.loads(ACESTREAM_MANIFEST.read_text(encoding="utf-8"))["platforms"])
    return [platform for platform in baseline if platform in supported]


def run(command: list[str], *, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    if not expect_success and result.returncode == 0:
        raise AssertionError(
            f"Command unexpectedly succeeded: {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_build_metadata(payload: dict, *, flavor: str, target: str, platforms: list[str], tags: list[str]) -> None:
    if payload.get("flavor") != flavor:
        raise AssertionError(f"expected flavor={flavor}, got {payload.get('flavor')!r}")
    if payload.get("target") != target:
        raise AssertionError(f"expected target={target}, got {payload.get('target')!r}")
    if payload.get("platforms") != platforms:
        raise AssertionError(f"expected platforms={platforms}, got {payload.get('platforms')!r}")
    if payload.get("tags") != tags:
        raise AssertionError(f"expected tags={tags}, got {payload.get('tags')!r}")
    if payload.get("target_tags") != tags:
        raise AssertionError(
            f"expected target_tags={tags}, got {payload.get('target_tags')!r}"
        )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        scraper_result = tmp_path / "scraper.json"
        acestream_result = tmp_path / "scraper-acestream.json"

        scraper_build = run(
            [
                "bash",
                str(BUILD_SCRIPT),
                "--dry-run",
                "--flavor",
                "scraper",
                "--tag",
                "example.com/acestream-scraper:test-scraper",
                "--tag",
                "example.com/acestream-scraper:test-scraper-alt",
                "--result-file",
                str(scraper_result),
            ]
        )
        if "Flavor: scraper" not in scraper_build.stdout:
            raise AssertionError("dry-run output did not report scraper flavor")
        scraper_payload = load_json(scraper_result)
        assert_build_metadata(
            scraper_payload,
            flavor="scraper",
            target="scraper",
            platforms=["linux/amd64", "linux/arm/v7", "linux/arm64"],
            tags=[
                "example.com/acestream-scraper:test-scraper",
                "example.com/acestream-scraper:test-scraper-alt",
            ],
        )

        acestream_build = run(
            [
                "bash",
                str(BUILD_SCRIPT),
                "--dry-run",
                "--flavor",
                "scraper-acestream",
                "--tag",
                "example.com/acestream-scraper:test-acestream",
                "--result-file",
                str(acestream_result),
            ]
        )
        expected_acestream_platforms = acestream_platforms()
        if f"Platforms: {','.join(expected_acestream_platforms)}" not in acestream_build.stdout:
            raise AssertionError(
                "dry-run output did not derive AceStream flavor platforms from the manifest"
            )
        for platform in expected_acestream_platforms:
            if f"AceStream engine for {platform}:" not in acestream_build.stdout:
                raise AssertionError(f"dry-run output did not report the engine source for {platform}")
        acestream_payload = load_json(acestream_result)
        assert_build_metadata(
            acestream_payload,
            flavor="scraper-acestream",
            target="scraper-acestream",
            platforms=expected_acestream_platforms,
            tags=["example.com/acestream-scraper:test-acestream"],
        )

        # A platform outside the baseline matrix must be rejected explicitly.
        invalid_platforms = run(
            [
                "bash",
                str(BUILD_SCRIPT),
                "--dry-run",
                "--flavor",
                "scraper-acestream",
                "--platforms",
                "linux/ppc64le",
            ],
            expect_success=False,
        )
        error_output = invalid_platforms.stdout + invalid_platforms.stderr
        if "does not support requested platforms" not in error_output:
            raise AssertionError("unsupported AceStream platform failure was not explicit")

        verify_scraper = run(
            [
                "bash",
                str(VERIFY_SCRIPT),
                "--result-file",
                str(scraper_result),
                "--flavor",
                "scraper",
            ]
        )
        if "Manifest verification passed." not in verify_scraper.stdout:
            raise AssertionError("scraper flavor verification did not pass")

        verify_acestream = run(
            [
                "bash",
                str(VERIFY_SCRIPT),
                "--result-file",
                str(acestream_result),
                "--flavor",
                "scraper-acestream",
            ]
        )
        expected_required = "Required platforms: " + ", ".join(sorted(expected_acestream_platforms))
        if expected_required not in verify_acestream.stdout:
            raise AssertionError("AceStream flavor verification did not derive expected platforms")

    print("Flavor-aware multiarch script validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

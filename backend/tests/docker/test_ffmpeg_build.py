"""Build the ffmpeg-builder stage for every image platform (cross-compiled on
the build host) and prove the binary works on the target: copy remux TS->HLS,
AC-3 -> AAC into fMP4 HLS, and the web player's exact ffmpeg command line, all
on a committed H.264+AC-3 fixture."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "backend" / "tests" / "docker" / "fixtures"
FIXTURE = FIXTURES / "sample-h264-ac3.m2ts"
PLATFORMS = ["linux/amd64", "linux/arm64", "linux/arm/v7"]

# The web player's command (spec 4.5), verbatim apart from the paths the
# service fills in. Building a binary that cannot run it is the failure this
# test exists to catch. It is a literal because this test runs inside a
# container against fixed paths; backend/tests/test_player_service.py's
# test_docker_build_test_runs_the_real_player_command fails if it drifts from
# PlayerService.ffmpeg_argv.
PLAYER_COMMAND = [
    "-nostdin", "-hide_banner", "-loglevel", "info", "-nostats",
    "-rw_timeout", "20000000", "-fflags", "+genpts+discardcorrupt",
    "-i", "/f/sample.m2ts",
    "-map", "0:v:0", "-map", "0:a:0?",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
    "-f", "hls", "-hls_time", "2", "-hls_list_size", "6", "-hls_delete_threshold", "2",
    "-hls_flags", "delete_segments+independent_segments+omit_endlist+temp_file",
    "-hls_segment_type", "mpegts", "-hls_segment_filename", "/out/player/seg%05d.ts",
    "/out/player/index.m3u8",
]


def _docker_available() -> bool:
    return shutil.which("docker") is not None and subprocess.run(["docker", "info"], capture_output=True).returncode == 0


pytestmark = pytest.mark.skipif(not _docker_available(), reason="docker not available on this runner")


def test_fixture_matches_pinned_sha256():
    sums = dict(reversed(line.split()) for line in (FIXTURES / "SHA256SUMS").read_text().splitlines() if line.strip())
    assert sums["sample-h264-ac3.m2ts"] == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()


@pytest.mark.parametrize("platform", PLATFORMS)
def test_ffmpeg_builder_produces_a_working_static_binary(tmp_path, platform):
    tag = f"acestream-scraper-ffmpeg:{platform.replace('/', '-')}-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        ["docker", "buildx", "build", "--platform", platform, "--network", "host", "--load",
         "--target", "ffmpeg-builder", "--tag", tag, str(REPO_ROOT)],
        check=True,
    )
    try:
        cid = subprocess.run(["docker", "create", "--platform", platform, tag], capture_output=True, text=True, check=True).stdout.strip()
        try:
            subprocess.run(["docker", "cp", f"{cid}:/out/.", str(tmp_path)], check=True)
        finally:
            subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
    finally:
        subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)
    ffmpeg = tmp_path / "ffmpeg"
    assert ffmpeg.is_file() and (tmp_path / "ffprobe").is_file()
    assert ffmpeg.stat().st_size < 16 * 1024 * 1024, "minimal build grew past 16 MB"

    # busybox carries no dynamic loader and no libc: only a fully static binary
    # can exec there, which is what the runtime image relies on.
    static = subprocess.run(
        ["docker", "run", "--rm", "--platform", platform, "--user", f"{os.getuid()}:{os.getgid()}",
         "-v", f"{tmp_path}:/ff:ro", "busybox:1.37", "/ff/ffmpeg", "-version"],
        capture_output=True, text=True, timeout=300,
    )
    assert static.returncode == 0, f"ffmpeg is not static: {static.stderr}"
    assert "ffmpeg version" in static.stdout, static.stdout

    out = tmp_path / "hls"
    (out / "player").mkdir(parents=True)
    # --user keeps everything written into the bind-mounted tmp_path owned by
    # the test runner instead of root, so pytest can clean the directory up.
    base = ["docker", "run", "--rm", "--platform", platform, "--user", f"{os.getuid()}:{os.getgid()}",
            "-v", f"{tmp_path}:/ff:ro", "-v", f"{FIXTURE}:/f/sample.m2ts:ro", "-v", f"{out}:/out",
            "python:3.13-slim"]
    # csv/flat writers repeat every stream once per program, so read the
    # unambiguous top-level "streams" array instead.
    probe = subprocess.run(base + ["/ff/ffprobe", "-v", "error", "-show_entries", "stream=codec_name", "-of", "json", "/f/sample.m2ts"],
                           capture_output=True, text=True, timeout=300)
    assert probe.returncode == 0, probe.stderr
    assert [stream["codec_name"] for stream in json.loads(probe.stdout)["streams"]] == ["h264", "ac3"], probe.stdout
    remux = subprocess.run(base + ["/ff/ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", "/f/sample.m2ts",
                                   "-c", "copy", "-f", "hls", "-hls_time", "1", "/out/copy.m3u8"], capture_output=True, text=True, timeout=300)
    assert remux.returncode == 0, remux.stderr
    assert (out / "copy.m3u8").exists() and list(out.glob("copy*.ts"))
    transcode = subprocess.run(base + ["/ff/ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", "/f/sample.m2ts",
                                       "-c:v", "copy", "-c:a", "aac", "-f", "hls", "-hls_time", "1",
                                       "-hls_segment_type", "fmp4", "/out/aac.m3u8"], capture_output=True, text=True, timeout=300)
    assert transcode.returncode == 0, transcode.stderr
    assert (out / "init.mp4").exists() and list(out.glob("aac*.m4s"))
    player = subprocess.run(base + ["/ff/ffmpeg"] + PLAYER_COMMAND, capture_output=True, text=True, timeout=300)
    assert player.returncode == 0, player.stderr
    assert (out / "player" / "index.m3u8").exists() and list((out / "player").glob("seg*.ts"))

# Media Integrations, Plan 2: ffmpeg Packaging and the Web Player — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a static minimal ffmpeg in every image flavor and an in-browser player: the backend turns an engine stream into HLS with ffmpeg (video copy, audio to AAC), the SPA plays it with hls.js from a dialog reachable from every channel surface.

**Architecture:** `docker/vendor/ffmpeg` + `docker/manifests/ffmpeg.json` feed a cross-compiling `ffmpeg-builder` Dockerfile stage whose output lands in `runtime-base` (`/opt/ffmpeg/bin`). `app/services/player_service.py` owns `PlayerSession`s (one shared ffmpeg per channel, an asyncio reaper/stat loop, PDEATHSIG-protected spawn, startup sweep); `app/api/endpoints/player.py` exposes session create/status/delete, the HLS files (with `?token=` propagation for native players) and capabilities. The frontend adds `hls.js` in its own chunk, `StreamPlayerDialog`, and Play actions on the Acestream Channels rows (Play visible, TV link in the menu), TV channel detail/table and Search.

**Tech Stack:** FFmpeg 8.1.2 (vendored source, static build), Debian cross toolchains, FastAPI/asyncio subprocess, httpx; React 18 + hls.js 1.7 + MUI; pytest, Jest, Playwright page objects.

**Spec:** `docs/superpowers/specs/2026-09-03-media-integrations-design.md` sections 4.5, 5, 8 (e2e notes). Plan 1 (`2026-09-03-media-integrations-1-foundation.md`) must be complete: it provides `Settings.PLAYER_*`/`FFMPEG_BINARY_PATH`, `EngineClient`, `engine_url_from_settings`, `EngineStats`, `ClosingStreamingResponse`, `buildPublicUrl`/`usePublicUrl`, `require_api_token` `?token=` handling and `/tuner/stream/<id>.ts`.

## Global Constraints

- Backend tests: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/<file>`; `client` fixture unless migration state matters. Docker tests under `backend/tests/docker` need a daemon and are excluded from the normal suite.
- Env knobs are read through `get_settings()` (`PLAYER_HLS_DIR` default `/tmp/acestream-player`, `PLAYER_MAX_SESSIONS` 3, `PLAYER_START_TIMEOUT_SECONDS` 45, `FFMPEG_BINARY_PATH` "" → `shutil.which("ffmpeg")`).
- Blocking work never runs on the event loop: the session-create endpoint is `async def` and runs its DB read and the engine JSON call in `run_in_threadpool`; ffmpeg is spawned on the loop thread (PDEATHSIG binds to the forking thread).
- HTTP 401 is reserved for the API token; player failures are `APIError` 502/409 with distinct codes (`PLAYER_LIMIT_REACHED` 409, `ENGINE_REFUSED`/`ENGINE_UNAVAILABLE` 502).
- ffmpeg command (exact): `ffmpeg -nostdin -hide_banner -loglevel info -nostats -rw_timeout 20000000 -fflags +genpts+discardcorrupt -i <playback_url> -map 0:v:0 -map 0:a:0? -c:v copy -c:a aac -b:a 160k -ac 2 -f hls -hls_time 2 -hls_list_size 6 -hls_delete_threshold 2 -hls_flags delete_segments+independent_segments+omit_endlist+temp_file -hls_segment_type mpegts -hls_segment_filename <dir>/seg%05d.ts <dir>/index.m3u8`.
- Frontend: TypeScript only, named prop interfaces, no `any`; `npm run lint -- --max-warnings=0`, `npm run typecheck`; row actions keep at most two visible icon buttons (Play, Check status); destructive actions use `useConfirm`; copy is plain language.
- OpenAPI dump + `npm run codegen` after DTO changes (Task 9); commit both artifacts.
- Commit trailers: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01NCvyzQfF1uXiozTEGgDvPM`. Branch `feature/media-integrations`. Never commit `docs/superpowers/` or `.superpowers/`.

---

### Task 1: Vendor the FFmpeg source and validate the manifest

**Files:**
- Create: `docker/vendor/ffmpeg/ffmpeg-8.1.2.tar.xz` (binary), `docker/vendor/ffmpeg/SHA256SUMS`, `docker/vendor/ffmpeg/README.md`, `docker/manifests/ffmpeg.json`
- Modify: `scripts/ci/validate_docker_manifest_metadata.py:143-146,183-206` (load + validate `ffmpeg.json`)
- Test: `backend/tests/docker/test_ffmpeg_vendor.py` (runs without Docker)

**Interfaces:**
- Produces: `docker/manifests/ffmpeg.json` with keys `version`, `vendor_dir`, `vendored_file`, `sha256`, `source_url`, `mirror_base_url`, `mirror_urls`; `validate_docker_manifest_metadata.py` fails when the vendored file/sums/manifest disagree.

- [ ] **Step 1: Obtain the tarball and write the failing test**

Copy the tarball if the session scratchpad still has it, else download it:

```bash
mkdir -p docker/vendor/ffmpeg
SRC=/private/tmp/claude-501/-Users-pipepito-Code-acestream-scraper-alt/e0cfdc1c-9746-456f-8132-efb0bc8a0a57/scratchpad/ffbuild/ffmpeg-8.1.2.tar.xz
[ -f "$SRC" ] && cp "$SRC" docker/vendor/ffmpeg/ || curl -fsSL -o docker/vendor/ffmpeg/ffmpeg-8.1.2.tar.xz https://ffmpeg.org/releases/ffmpeg-8.1.2.tar.xz
shasum -a 256 docker/vendor/ffmpeg/ffmpeg-8.1.2.tar.xz
```
Expected digest: `464beb5e7bf0c311e68b45ae2f04e9cc2af88851abb4082231742a74d97b524c` (if it differs, stop and report — the pin below must match the file).

Create `backend/tests/docker/test_ffmpeg_vendor.py`:

```python
"""The FFmpeg source tarball is vendored (docker/vendor/ffmpeg) so image
builds need no egress to ffmpeg.org: manifest, SHA256SUMS and the archive
must agree, the validator must check them, and the build script must hand
the archive to the Dockerfile for every flavor (ffmpeg rides in runtime-base)."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "docker" / "manifests" / "ffmpeg.json"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh"
VALIDATOR = REPO_ROOT / "scripts" / "ci" / "validate_docker_manifest_metadata.py"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_vendored_archive_matches_manifest_and_sums():
    manifest = _manifest()
    vendor_dir = REPO_ROOT / manifest["vendor_dir"]
    archive = vendor_dir / manifest["vendored_file"]
    assert archive.is_file(), f"vendored archive missing: {archive}"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["sha256"]
    sums = {}
    for line in (vendor_dir / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            checksum, name = line.split(maxsplit=1)
            sums[name.strip().lstrip("*")] = checksum
    assert sums.get(manifest["vendored_file"]) == manifest["sha256"]
    assert manifest["version"] in manifest["vendored_file"]
    assert manifest["vendor_dir"] == "docker/vendor/ffmpeg"
    assert manifest["mirror_urls"][0].endswith("/" + manifest["vendored_file"])


def test_validator_checks_the_ffmpeg_manifest(tmp_path):
    proc = subprocess.run(["python3", str(VALIDATOR)], capture_output=True, text=True, cwd=REPO_ROOT)
    assert proc.returncode == 0, proc.stderr
    # Break the sha in a copy of the repo layout the validator reads relative to itself:
    # simplest is to assert the validator source references ffmpeg.json and require_vendored for it.
    source = VALIDATOR.read_text()
    assert 'load_json("docker/manifests/ffmpeg.json")' in source
    assert 'require_vendored(\n        "ffmpeg.json"' in source or 'require_vendored("ffmpeg.json"' in source


def test_build_script_passes_vendored_ffmpeg_for_every_flavor():
    manifest = _manifest()
    for flavor in ("scraper", "scraper-acestream", "scraper-acexy", "scraper-acestream-acexy"):
        proc = subprocess.run(
            ["bash", str(BUILD_SCRIPT), "--flavor", flavor, "--platforms", "linux/amd64", "--dry-run"],
            capture_output=True, text=True, cwd=REPO_ROOT, check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert f"FFMPEG_VENDORED_FILE={manifest['vendored_file']}" in proc.stdout, flavor
        assert f"FFMPEG_SHA256={manifest['sha256']}" in proc.stdout, flavor
        assert f"FFMPEG_SOURCE_URL={manifest['source_url']}" in proc.stdout, flavor


def test_dockerfile_builds_ffmpeg_from_the_vendored_archive():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    builder = dockerfile.split("AS ffmpeg-builder", 1)[1].split("\nFROM ", 1)[0]
    assert "FFMPEG_VENDORED_FILE" in builder and "FFMPEG_SHA256" in builder
    assert "--mount=type=bind,source=docker/vendor,target=/tmp/ffmpeg-vendor,readonly" in builder
    assert "build-ffmpeg.sh" in builder
    assert "COPY --from=ffmpeg-builder /out/ /opt/ffmpeg/bin/" in dockerfile
```

- [ ] **Step 2: Run it to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_vendor.py`
Expected: FAIL (manifest missing). The build-script and Dockerfile tests keep failing until Task 2.

- [ ] **Step 3: Manifest, sums, README**

`docker/manifests/ffmpeg.json`:

```json
{
  "version": "8.1.2",
  "vendor_dir": "docker/vendor/ffmpeg",
  "vendored_file": "ffmpeg-8.1.2.tar.xz",
  "sha256": "464beb5e7bf0c311e68b45ae2f04e9cc2af88851abb4082231742a74d97b524c",
  "source_url": "https://ffmpeg.org/releases/ffmpeg-8.1.2.tar.xz",
  "mirror_base_url": "https://github.com/Pipepito/acestream-scraper/releases/download/acestream-binaries-ffmpeg-8.1.2",
  "mirror_urls": [
    "https://github.com/Pipepito/acestream-scraper/releases/download/acestream-binaries-ffmpeg-8.1.2/ffmpeg-8.1.2.tar.xz"
  ]
}
```

`docker/vendor/ffmpeg/SHA256SUMS`:

```
464beb5e7bf0c311e68b45ae2f04e9cc2af88851abb4082231742a74d97b524c  ffmpeg-8.1.2.tar.xz
```

`docker/vendor/ffmpeg/README.md`:

```markdown
# Vendored FFmpeg source

Source tarball of the FFmpeg release pinned in `docker/manifests/ffmpeg.json`.
The `ffmpeg-builder` stage of the root `Dockerfile` cross-compiles a minimal
static `ffmpeg`/`ffprobe` from it (`docker/scripts/build-ffmpeg.sh`) for every
image platform, so builds need no egress to ffmpeg.org and no apt `ffmpeg`
(which would add 300-460 MB per image).

| File | Upstream source |
| --- | --- |
| `ffmpeg-8.1.2.tar.xz` | https://ffmpeg.org/releases/ffmpeg-8.1.2.tar.xz |

`SHA256SUMS` holds the checksum; it must equal `sha256` in the manifest. The
same file is a GitHub Release asset on the tag named by `mirror_base_url`
(upload it there when bumping: the build script's download ladder is vendored
copy → `source_url` → `mirror_urls`).

## What the build enables

Only what the web player needs: demuxers mpegts/hls/mov/matroska/aac/mp3/ac3/
mpegvideo/h264/hevc, muxers hls/mpegts/mp4/segment, decoders h264/hevc/aac/
aac_latm/ac3/eac3/mp2/mp3/mpeg2video, the native `aac` encoder, protocols
file/pipe/http/tcp/unix. No TLS, no libx264, no hardware acceleration
(users who need more can mount their own binary and set `FFMPEG_BINARY_PATH`).

## Bumping the pin

1. Download `https://ffmpeg.org/releases/ffmpeg-<version>.tar.xz` here.
2. Update `SHA256SUMS` and `docker/manifests/ffmpeg.json` (`version`,
   `vendored_file`, `sha256`, `source_url`, `mirror_base_url`, `mirror_urls`).
3. Run `python3 scripts/ci/validate_docker_manifest_metadata.py` and
   `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_vendor.py backend/tests/docker/test_ffmpeg_build.py`.
4. Upload the tarball to the release tag and remove the previous archive.
```

- [ ] **Step 4: Validator**

In `scripts/ci/validate_docker_manifest_metadata.py` update the module docstring to mention `ffmpeg.json`, and in `main()` after the acexy block (before `ace_stream_platforms = ...`) add:

```python
    ffmpeg = load_json("docker/manifests/ffmpeg.json")
    require_keys(ffmpeg, ["version", "vendor_dir", "vendored_file", "sha256", "source_url", "mirror_base_url", "mirror_urls"], "ffmpeg.json")
    if not isinstance(ffmpeg["sha256"], str) or not SHA256_RE.match(ffmpeg["sha256"]):
        raise AssertionError("ffmpeg.json sha256 must be a 64-hex string")
    if ffmpeg["vendor_dir"] != "docker/vendor/ffmpeg":
        raise AssertionError("ffmpeg.json vendor_dir must be docker/vendor/ffmpeg (the Dockerfile mounts docker/vendor)")
    if not str(ffmpeg["source_url"]).startswith("https://"):
        raise AssertionError("ffmpeg.json source_url must be https")
    require_vendored(
        "ffmpeg.json",
        ffmpeg["vendor_dir"],
        ffmpeg["vendored_file"],
        ffmpeg["sha256"],
        ffmpeg["mirror_urls"],
        ffmpeg["mirror_base_url"],
    )
```

- [ ] **Step 5: Run**

Run: `python3 scripts/ci/validate_docker_manifest_metadata.py && PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_vendor.py -k "matches or validator"`
Expected: PASS (the two Dockerfile/build-script tests still fail until Task 2).

- [ ] **Step 6: Commit**

```bash
git add docker/vendor/ffmpeg docker/manifests/ffmpeg.json scripts/ci/validate_docker_manifest_metadata.py backend/tests/docker/test_ffmpeg_vendor.py
git commit -m "build(ffmpeg): vendor the FFmpeg 8.1.2 source with manifest and validation"
```

---

### Task 2: `ffmpeg-builder` stage, build script, runtime wiring, docker smoke test

**Files:**
- Create: `docker/scripts/build-ffmpeg.sh`, `backend/tests/docker/fixtures/sample-h264-ac3.m2ts`, `backend/tests/docker/fixtures/SHA256SUMS`, `backend/tests/docker/fixtures/README.md`, `backend/tests/docker/test_ffmpeg_build.py`
- Modify: `Dockerfile` (new stage before `runtime-base`; `runtime-base` COPY + ENV), `scripts/ci/build_multiarch_images.sh` (derive `FFMPEG_*` build args for every flavor), `entrypoint.sh` (`IMAGE_HAS_FFMPEG`), `.gitattributes`, `Jenkinsfile` (smoke stage), `backend/tests/test_runtime_integration_guards.py`, `docs/ops/multiarch-manifest-updates.md`

**Interfaces:**
- Produces: `/opt/ffmpeg/bin/ffmpeg` + `ffprobe` in every image; `ENV FFMPEG_BINARY_PATH=/opt/ffmpeg/bin/ffmpeg`; entrypoint export `IMAGE_HAS_FFMPEG=true|false` (from `-x "$FFMPEG_BINARY_PATH"`); build args `FFMPEG_VENDORED_FILE`, `FFMPEG_SHA256`, `FFMPEG_SOURCE_URL`, `FFMPEG_MIRROR_URLS` (space-separated).

- [ ] **Step 1: Write the failing guard tests**

Append to `backend/tests/test_runtime_integration_guards.py`:

```python
def test_entrypoint_detects_bundled_ffmpeg():
    entrypoint = (REPO_ROOT / "entrypoint.sh").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    assert 'FFMPEG_BINARY_PATH="${FFMPEG_BINARY_PATH:-/opt/ffmpeg/bin/ffmpeg}"' in entrypoint
    assert 'if [ -x "$FFMPEG_BINARY_PATH" ]; then IMAGE_HAS_FFMPEG=true; else IMAGE_HAS_FFMPEG=false; fi' in entrypoint
    assert "IMAGE_HAS_FFMPEG" in entrypoint.split("export ENABLE_WARP", 1)[1].split("\n", 1)[0]
    assert "FFMPEG_BINARY_PATH=/opt/ffmpeg/bin/ffmpeg" in dockerfile
    assert "FROM --platform=$BUILDPLATFORM debian:trixie-slim AS ffmpeg-builder" in dockerfile


def test_jenkins_smoke_stage_runs_the_ffmpeg_build_test():
    pipeline = (REPO_ROOT / "Jenkinsfile").read_text()
    assert "backend/tests/docker/test_ffmpeg_build.py" in pipeline
    assert "backend/tests/docker/test_ffmpeg_vendor.py" in pipeline
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_runtime_integration_guards.py -k "ffmpeg"`
Expected: FAIL.

- [ ] **Step 3: The build script**

Create `docker/scripts/build-ffmpeg.sh` (mode 0755):

```bash
#!/usr/bin/env bash
# Build a minimal static ffmpeg/ffprobe for the image platform being built.
# Runs inside the Dockerfile's `ffmpeg-builder` stage on $BUILDPLATFORM and
# cross-compiles with the Debian toolchains, so no QEMU is involved.
#
# Source resolution (same ladder as install-acestream.sh): the vendored
# tarball under /tmp/ffmpeg-vendor/ffmpeg (bind-mounted docker/vendor) ->
# FFMPEG_SOURCE_URL -> each FFMPEG_MIRROR_URLS entry; sha256-verified against
# FFMPEG_SHA256 (or against the adjacent SHA256SUMS when the build-args are
# empty, e.g. a plain `docker build`).
#
# Output: /out/ffmpeg and /out/ffprobe (stripped, fully static).
set -euo pipefail

TARGETARCH="${TARGETARCH:?TARGETARCH is not set (pass --platform to docker buildx build)}"
TARGETVARIANT="${TARGETVARIANT:-}"
VENDOR_DIR="${FFMPEG_VENDOR_DIR:-/tmp/ffmpeg-vendor/ffmpeg}"
OUT_DIR="${FFMPEG_OUT_DIR:-/out}"
WORK="${FFMPEG_WORK_DIR:-/tmp/ffmpeg-build}"
VENDORED_FILE="${FFMPEG_VENDORED_FILE:-}"
SHA256="${FFMPEG_SHA256:-}"
SOURCE_URL="${FFMPEG_SOURCE_URL:-}"
MIRROR_URLS="${FFMPEG_MIRROR_URLS:-}"

log() { printf 'build-ffmpeg: %s\n' "$*"; }
fail() { printf 'build-ffmpeg: %s\n' "$*" >&2; exit 1; }

mkdir -p "$OUT_DIR" "$WORK"

# --- resolve the tarball ----------------------------------------------------
if [ -z "$VENDORED_FILE" ]; then
    # Plain docker build without build-args: take the single vendored tarball.
    candidates=("$VENDOR_DIR"/ffmpeg-*.tar.xz)
    [ ${#candidates[@]} -eq 1 ] && [ -f "${candidates[0]}" ] || fail "expected exactly one ffmpeg-*.tar.xz under $VENDOR_DIR"
    VENDORED_FILE="$(basename "${candidates[0]}")"
    SHA256="$(grep " ${VENDORED_FILE}\$" "$VENDOR_DIR/SHA256SUMS" | awk '{print $1}')"
    [ -n "$SHA256" ] || fail "no SHA256SUMS entry for $VENDORED_FILE"
fi
TARBALL="$WORK/$VENDORED_FILE"
if [ -f "$VENDOR_DIR/$VENDORED_FILE" ]; then
    log "using vendored $VENDORED_FILE"
    cp "$VENDOR_DIR/$VENDORED_FILE" "$TARBALL"
else
    # shellcheck disable=SC2086  # mirror list is intentionally word-split
    for url in $SOURCE_URL $MIRROR_URLS; do
        log "downloading $url"
        if curl -fsSL --retry 3 --retry-delay 5 --connect-timeout 30 -o "$TARBALL" "$url"; then break; fi
        rm -f "$TARBALL"
    done
    [ -f "$TARBALL" ] || fail "could not obtain $VENDORED_FILE from the vendored copy, the upstream URL or any mirror"
fi
printf '%s  %s\n' "$SHA256" "$TARBALL" | sha256sum -c - >/dev/null || fail "sha256 mismatch for $VENDORED_FILE"

# --- toolchain ---------------------------------------------------------------
host_arch="$(dpkg --print-architecture)"
case "$TARGETARCH" in
    amd64) target_triplet=x86_64-linux-gnu; ff_arch=x86_64; extra_cflags="" ;;
    arm64) target_triplet=aarch64-linux-gnu; ff_arch=aarch64; extra_cflags="" ;;
    arm)   target_triplet=arm-linux-gnueabihf; ff_arch=arm; extra_cflags="-march=armv7-a -mfpu=neon -mfloat-abi=hard" ;;
    *) fail "unsupported TARGETARCH: $TARGETARCH" ;;
esac
cross_args=()
if [ "$TARGETARCH" != "$host_arch" ]; then
    cross_args=(--enable-cross-compile --arch="$ff_arch" --target-os=linux --cross-prefix="${target_triplet}-")
    [ "$TARGETARCH" = "arm" ] && cross_args+=(--cpu=armv7-a)
    STRIP="${target_triplet}-strip"
else
    STRIP=strip
fi

# --- configure + build -------------------------------------------------------
SRC="$WORK/src"
rm -rf "$SRC"; mkdir -p "$SRC"
tar -xJf "$TARBALL" -C "$SRC" --strip-components=1
cd "$SRC"
./configure \
    --prefix=/usr/local \
    --disable-everything --disable-doc --disable-debug --disable-programs \
    --enable-ffmpeg --enable-ffprobe \
    --disable-avdevice --disable-autodetect \
    --enable-static --disable-shared --extra-ldflags=-static --pkg-config-flags=--static \
    --enable-demuxer=mpegts,hls,mov,matroska,aac,mp3,ac3,mpegvideo,h264,hevc,data \
    --enable-muxer=hls,mpegts,mp4,segment,stream_segment,null \
    --enable-decoder=h264,hevc,aac,aac_latm,ac3,eac3,mp2,mp3,mpeg2video \
    --enable-encoder=aac \
    --enable-parser=h264,hevc,aac,aac_latm,ac3,mpegaudio,mpegvideo \
    --enable-bsf=aac_adtstoasc,h264_mp4toannexb,hevc_mp4toannexb,extract_extradata,dump_extradata,setts \
    --enable-filter=aformat,aresample,anull,null,copy,format,scale,asetnsamples,volume \
    --enable-protocol=file,pipe,http,tcp,unix,data,crypto \
    ${extra_cflags:+--extra-cflags="$extra_cflags"} \
    "${cross_args[@]}" > "$WORK/configure.log" 2>&1 || { tail -40 "$WORK/configure.log" >&2; fail "configure failed"; }
make -j"$(nproc)" > "$WORK/make.log" 2>&1 || { tail -40 "$WORK/make.log" >&2; fail "make failed"; }
"$STRIP" ffmpeg ffprobe
install -m 0755 ffmpeg "$OUT_DIR/ffmpeg"
install -m 0755 ffprobe "$OUT_DIR/ffprobe"
printf 'ffmpeg_version=%s\ntargetarch=%s\ntargetvariant=%s\nsha256=%s\n' \
    "${VENDORED_FILE#ffmpeg-}" "$TARGETARCH" "$TARGETVARIANT" "$SHA256" > "$OUT_DIR/install-metadata.txt"
log "built static ffmpeg for $TARGETARCH${TARGETVARIANT:+/$TARGETVARIANT}: $(stat -c %s "$OUT_DIR/ffmpeg") bytes"
```

- [ ] **Step 4: Dockerfile stage and runtime wiring**

Insert before `FROM python:${APP_PYTHON_VERSION}-slim AS runtime-base` (after the `acexy-builder` stage):

```dockerfile
# Minimal static ffmpeg for the web player (spec 4.5): cross-compiled on the
# build host with Debian's toolchains (no QEMU), ~5-10 MB, no runtime deps.
# The vendored source is bind-mounted, not copied into a layer.
FROM --platform=$BUILDPLATFORM debian:trixie-slim AS ffmpeg-builder

ARG TARGETARCH
ARG TARGETVARIANT
ARG FFMPEG_VENDORED_FILE
ARG FFMPEG_SHA256
ARG FFMPEG_SOURCE_URL
ARG FFMPEG_MIRROR_URLS

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl make nasm pkg-config xz-utils \
    && host="$(dpkg --print-architecture)" \
    && case "${TARGETARCH}:${host}" in \
        amd64:amd64|arm64:arm64) ;; \
        amd64:*) apt-get install -y --no-install-recommends gcc-x86-64-linux-gnu libc6-dev-amd64-cross ;; \
        arm64:*) apt-get install -y --no-install-recommends gcc-aarch64-linux-gnu libc6-dev-arm64-cross ;; \
        arm:*)   apt-get install -y --no-install-recommends gcc-arm-linux-gnueabihf libc6-dev-armhf-cross ;; \
       esac \
    && rm -rf /var/lib/apt/lists/*

COPY docker/scripts/build-ffmpeg.sh /usr/local/lib/ffmpeg-build/build-ffmpeg.sh
RUN --mount=type=bind,source=docker/vendor,target=/tmp/ffmpeg-vendor,readonly \
    chmod +x /usr/local/lib/ffmpeg-build/build-ffmpeg.sh \
    && TARGETARCH="${TARGETARCH}" TARGETVARIANT="${TARGETVARIANT}" \
       FFMPEG_VENDORED_FILE="${FFMPEG_VENDORED_FILE}" FFMPEG_SHA256="${FFMPEG_SHA256}" \
       FFMPEG_SOURCE_URL="${FFMPEG_SOURCE_URL}" FFMPEG_MIRROR_URLS="${FFMPEG_MIRROR_URLS}" \
       /usr/local/lib/ffmpeg-build/build-ffmpeg.sh
```

In `runtime-base`: add `FFMPEG_BINARY_PATH=/opt/ffmpeg/bin/ffmpeg` to the big `ENV` block (after `IPFS_GATEWAY_PORT=8081` — mind the trailing backslash), and after the ZeroNet `COPY --from=zeronet-installer ... RUN ...` block add:

```dockerfile
# Static ffmpeg/ffprobe for the web player (every flavor and platform).
COPY --from=ffmpeg-builder /out/ /opt/ffmpeg/bin/
```

`entrypoint.sh` — after the IPFS detection block (line ~222) add:

```bash
# The web player needs ffmpeg; every image ships a static build, but a
# custom mount (or bare-metal run) may not — detect it like IPFS/ZeroNet.
FFMPEG_BINARY_PATH="${FFMPEG_BINARY_PATH:-/opt/ffmpeg/bin/ffmpeg}"
if [ -z "${IMAGE_HAS_FFMPEG:-}" ]; then
    if [ -x "$FFMPEG_BINARY_PATH" ]; then IMAGE_HAS_FFMPEG=true; else IMAGE_HAS_FFMPEG=false; fi
fi
IMAGE_HAS_FFMPEG=$(normalize_bool "$IMAGE_HAS_FFMPEG")
```

and extend the export line to `export ENABLE_WARP ENABLE_ACESTREAM_ENGINE ENABLE_ACEXY ENABLE_IPFS ENABLE_ZERONET ENABLE_TOR IMAGE_HAS_ACESTREAM IMAGE_HAS_ACEXY IMAGE_HAS_IPFS IMAGE_HAS_ZERONET IMAGE_HAS_FFMPEG IPFS_BINARY_PATH ZERONET_BINARY_PATH FFMPEG_BINARY_PATH`.

`scripts/ci/build_multiarch_images.sh` — after the Acexy derivation loop (before the `--load` single-platform check) add:

```bash
# ffmpeg rides in runtime-base, so every flavor gets the vendored source
# (sha256-verified in the ffmpeg-builder stage).
FFMPEG_MANIFEST="${FFMPEG_MANIFEST:-$ROOT_DIR/docker/manifests/ffmpeg.json}"
if [[ ! -f "$FFMPEG_MANIFEST" ]]; then
    echo "ffmpeg manifest not found: $FFMPEG_MANIFEST" >&2
    exit 1
fi
if ! ffmpeg_derived="$(python3 - "$FFMPEG_MANIFEST" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
for key in ("vendored_file", "sha256", "source_url", "mirror_urls"):
    if not m.get(key):
        raise SystemExit(f"ffmpeg manifest missing required key: {key}")
print(f"FFMPEG_VENDORED_FILE={m['vendored_file']}")
print(f"FFMPEG_SHA256={m['sha256']}")
print(f"FFMPEG_SOURCE_URL={m['source_url']}")
print("FFMPEG_MIRROR_URLS=" + " ".join(m["mirror_urls"]))
PY
)"; then
    printf 'ERROR: failed to derive ffmpeg build args\n%s\n' "$ffmpeg_derived" >&2
    exit 1
fi
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    key="${line%%=*}"
    already=0
    for existing in "${BUILD_ARGS[@]:-}"; do
        if [[ "$existing" == "$key="* ]]; then already=1; break; fi
    done
    if [[ "$already" -eq 0 ]]; then BUILD_ARGS+=("--build-arg" "$line"); fi
done <<< "$ffmpeg_derived"
```

Check how the dry-run prints build args (grep `print_plan_header`/`BUILD_ARGS` in the script) so `FFMPEG_VENDORED_FILE=...` appears on stdout in `--dry-run` like the Acexy args do (the Acexy vendor test relies on that; reuse the same printing path).

`.gitattributes` — append:

```
backend/tests/docker/fixtures/** binary
backend/tests/docker/fixtures/**/README.md text
backend/tests/docker/fixtures/**/SHA256SUMS text
```

- [ ] **Step 5: The fixture**

Generate a 2-second H.264 + AC-3 transport stream with a full ffmpeg from a container (the minimal binary has no encoders):

```bash
mkdir -p backend/tests/docker/fixtures
docker run --rm -v "$PWD/backend/tests/docker/fixtures:/out" lscr.io/linuxserver/ffmpeg:latest \
  -f lavfi -i testsrc2=size=64x64:rate=5 -f lavfi -i sine=frequency=440:sample_rate=48000 \
  -t 2 -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a ac3 -b:a 64k -f mpegts /out/sample-h264-ac3.m2ts
(cd backend/tests/docker/fixtures && shasum -a 256 sample-h264-ac3.m2ts > SHA256SUMS && cat SHA256SUMS && ls -la)
```
Expected: a file of roughly 30-80 KB. Write `backend/tests/docker/fixtures/README.md` with that exact one-liner and the sentence "Regenerate only with a full ffmpeg; the image's minimal build has no video or AC-3 encoders. `.m2ts` keeps TypeScript tooling globs away from the file."

- [ ] **Step 6: The docker build test**

Create `backend/tests/docker/test_ffmpeg_build.py`:

```python
"""Build the ffmpeg-builder stage for every image platform (cross-compiled on
the build host) and prove the binary works on the target: copy remux TS->HLS
and AC-3 -> AAC into fMP4 HLS on a committed H.264+AC-3 fixture."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "backend" / "tests" / "docker" / "fixtures"
FIXTURE = FIXTURES / "sample-h264-ac3.m2ts"
PLATFORMS = ["linux/amd64", "linux/arm64", "linux/arm/v7"]


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

    out = tmp_path / "hls"
    out.mkdir()
    base = ["docker", "run", "--rm", "--platform", platform,
            "-v", f"{tmp_path}:/ff:ro", "-v", f"{FIXTURE}:/f/sample.m2ts:ro", "-v", f"{out}:/out",
            "python:3.13-slim"]
    probe = subprocess.run(base + ["/ff/ffprobe", "-v", "error", "-show_entries", "stream=codec_name", "-of", "csv=p=0", "/f/sample.m2ts"],
                           capture_output=True, text=True, timeout=300)
    assert probe.returncode == 0, probe.stderr
    assert probe.stdout.split() == ["h264", "ac3"], probe.stdout
    remux = subprocess.run(base + ["/ff/ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", "/f/sample.m2ts",
                                   "-c", "copy", "-f", "hls", "-hls_time", "1", "/out/copy.m3u8"], capture_output=True, text=True, timeout=300)
    assert remux.returncode == 0, remux.stderr
    assert (out / "copy.m3u8").exists() and list(out.glob("copy*.ts"))
    transcode = subprocess.run(base + ["/ff/ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", "/f/sample.m2ts",
                                       "-c:v", "copy", "-c:a", "aac", "-f", "hls", "-hls_time", "1",
                                       "-hls_segment_type", "fmp4", "/out/aac.m3u8"], capture_output=True, text=True, timeout=300)
    assert transcode.returncode == 0, transcode.stderr
    assert (out / "init.mp4").exists() and list(out.glob("aac*.m4s"))
```

- [ ] **Step 7: Jenkins and docs**

`Jenkinsfile`, smoke stage: after the `test_install_acestream.py` line add:

```bash
# The web player's static ffmpeg must build for every platform and run on it.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_vendor.py backend/tests/docker/test_ffmpeg_build.py -v
```

`docs/ops/multiarch-manifest-updates.md` — add a section "ffmpeg (`docker/manifests/ffmpeg.json`)" listing the keys, that it applies to every flavor via `runtime-base`, and the bump steps (pointing at `docker/vendor/ffmpeg/README.md`).

- [ ] **Step 8: Build locally and run the tests**

Run:
```bash
python3 scripts/ci/validate_docker_manifest_metadata.py
bash scripts/ci/validate_command_builder.sh
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_vendor.py backend/tests/test_runtime_integration_guards.py -k "ffmpeg or vendored or dockerfile"
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_build.py -k "arm64 or fixture"   # native on this Mac; run the amd64/arm/v7 cases too if time allows (QEMU)
```
Expected: PASS. The full-image build is not required here (the smoke test in CI builds it), but do run `docker buildx build --platform linux/arm64 --target runtime-base --load -t spike-runtime-base .` once and `docker run --rm spike-runtime-base /opt/ffmpeg/bin/ffmpeg -version | head -1` to confirm the COPY path, then `docker image rm spike-runtime-base`.

- [ ] **Step 9: Commit**

```bash
git add Dockerfile docker/scripts/build-ffmpeg.sh scripts/ci/build_multiarch_images.sh entrypoint.sh .gitattributes Jenkinsfile docs/ops/multiarch-manifest-updates.md backend/tests/docker/fixtures backend/tests/docker/test_ffmpeg_build.py backend/tests/test_runtime_integration_guards.py
git commit -m "build(ffmpeg): cross-compiled static ffmpeg in every image with a per-platform smoke test"
```

---

### Task 3: Player session service (backend core)

**Files:**
- Create: `backend/app/services/player_service.py`, `backend/tests/fake_ffmpeg.py`
- Test: `backend/tests/test_player_service.py`

**Interfaces:**
- Produces:
  ```python
  PlayerState = Literal["starting", "ready", "error", "stopped"]
  PlayerError = Literal["engine_unavailable", "engine_refused", "engine_stalled", "ffmpeg_missing", "ffmpeg_failed"]
  @dataclass class PlayerSession: id, content_id, state, error, error_message, created_at, last_access, viewers, viewers_zero_since, dir (Path), engine_session, process, codecs: dict[str, str|None] ({"video":..,"audio":..}), stats: EngineStats|None, stderr_tail: deque[str]
  class PlayerLimitReached(RuntimeError): limit, active
  class PlayerService:
      def __init__(self, *, settings_getter=get_settings, engine_factory: Callable[[], EngineClient], ffmpeg_path: Optional[str] = None, monotonic=time.monotonic)
      def ffmpeg_path(self) -> Optional[str]
      def capabilities(self) -> dict
      async def start(self) -> None ; async def stop(self) -> None
      async def open_session(self, content_id: str) -> PlayerSession   # create or join; raises PlayerLimitReached
      def get(self, session_id: str) -> Optional[PlayerSession]
      def touch(self, session_id: str) -> None
      def leave(self, session_id: str) -> None
      def list_sessions(self) -> list[PlayerSession]
      def hls_ready(self, session) -> bool
      def playlist_path(self, session) -> Path
      async def tick(self) -> None     # one reaper/stat iteration (tests call it directly)
  player_service = PlayerService(engine_factory=_engine_from_settings)  # module singleton; engine_factory opens its own DB session
  ```

- [ ] **Step 1: The fake ffmpeg and the failing tests**

Create `backend/tests/fake_ffmpeg.py` (executable; tests pass its path as `ffmpeg_path`):

```python
#!/usr/bin/env python3
"""Stand-in for ffmpeg in player tests. Reads the output playlist path from
the last argv entry, prints a codec dump like ffmpeg does, then writes HLS
segments until it is terminated. Behaviour switches via env FAKE_FFMPEG_MODE:
  normal (default) | never_ready | exit_early | flood_stderr
"""
import os
import signal
import sys
import time
from pathlib import Path

mode = os.environ.get("FAKE_FFMPEG_MODE", "normal")
playlist = Path(sys.argv[-1])
directory = playlist.parent
directory.mkdir(parents=True, exist_ok=True)

sys.stderr.write("Input #0, mpegts, from 'http://engine':\n")
sys.stderr.write("  Stream #0:0[0x100]: Video: %s (High) ([27][0][0][0] / 0x001B), yuv420p, 1920x1080\n" % os.environ.get("FAKE_FFMPEG_VIDEO", "h264"))
sys.stderr.write("  Stream #0:1[0x101]: Audio: %s ([129][0][0][0] / 0x0081), 48000 Hz, stereo\n" % os.environ.get("FAKE_FFMPEG_AUDIO", "ac3"))
sys.stderr.flush()

if mode == "exit_early":
    sys.stderr.write("Error opening input: Connection refused\n")
    sys.exit(1)

running = True

def _term(*_):
    global running
    running = False

signal.signal(signal.SIGTERM, _term)
seq = 0
while running:
    if mode == "flood_stderr" and seq < 400:
        sys.stderr.write("\r" + ("frame=%d fps=25 q=-1.0 size=1024kB time=00:00:01.00 bitrate=8192kbits/s speed=1x" % seq) * 4)
        sys.stderr.flush()
    if mode != "never_ready":
        seg = directory / f"seg{seq:05d}.ts"
        seg.write_bytes(b"\x47" + b"\x00" * 187)
        keep = list(range(max(0, seq - 5), seq + 1))
        tmp = playlist.with_suffix(".m3u8.tmp")
        tmp.write_text("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n#EXT-X-MEDIA-SEQUENCE:%d\n" % keep[0]
                       + "".join("#EXTINF:2.000000,\nseg%05d.ts\n" % i for i in keep))
        os.replace(tmp, playlist)
        for old in directory.glob("seg*.ts"):
            if int(old.stem[3:]) < keep[0]:
                old.unlink(missing_ok=True)
        seq += 1
    time.sleep(0.05)
sys.exit(0)
```

Create `backend/tests/test_player_service.py`:

```python
"""PlayerService: sessions, ffmpeg lifecycle, state machine, reaper (spec 5.1)."""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.services.engine_client import EngineClient, EngineRefusedError
from app.services.player_service import PlayerLimitReached, PlayerService

FAKE_FFMPEG = Path(__file__).parent / "fake_ffmpeg.py"
IH = "0" * 40
IH2 = "1" * 40


class FakeSettings:
    def __init__(self, hls_dir, max_sessions=3, start_timeout=45):
        self.PLAYER_HLS_DIR = str(hls_dir)
        self.PLAYER_MAX_SESSIONS = max_sessions
        self.PLAYER_START_TIMEOUT_SECONDS = start_timeout
        self.FFMPEG_BINARY_PATH = ""


def _engine(handler=None):
    def default(request):
        p = request.url.path
        if p == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        if "/ace/stat/" in p:
            return httpx.Response(200, json={"response": {"status": "dl", "peers": 3, "speed_down": 500, "speed_up": 10}, "error": None})
        return httpx.Response(200, text="ok")
    return EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler or default)))


@pytest.fixture
def make_service(tmp_path, monkeypatch):
    def factory(mode="normal", ffmpeg=str(FAKE_FFMPEG), handler=None, **settings):
        monkeypatch.setenv("FAKE_FFMPEG_MODE", mode)
        clock = {"now": 1000.0}
        svc = PlayerService(
            settings_getter=lambda: FakeSettings(tmp_path / "hls", **settings),
            engine_factory=lambda: _engine(handler),
            ffmpeg_path=ffmpeg,
            monotonic=lambda: clock["now"],
        )
        svc._clock = clock  # test hook to advance time
        return svc
    return factory


async def _wait(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return False


def test_open_session_spawns_ffmpeg_and_becomes_ready(make_service):
    svc = make_service()

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert s.state == "starting" and s.viewers == 1
            assert s.process is not None and (s.dir / "ffmpeg.pid").exists()
            assert await _wait(lambda: svc.hls_ready(s))
            await svc.tick()
            assert s.state == "ready"
            assert s.codecs == {"video": "h264", "audio": "ac3"}
            assert s.stats is not None and s.stats.peers == 3
            joined = await svc.open_session(IH)
            assert joined is s and s.viewers == 2
        finally:
            await svc.stop()
    asyncio.run(run())


def test_limit_reached(make_service):
    svc = make_service(max_sessions=1)

    async def run():
        await svc.start()
        try:
            await svc.open_session(IH)
            with pytest.raises(PlayerLimitReached) as exc:
                await svc.open_session(IH2)
            assert exc.value.limit == 1 and exc.value.active == 1
        finally:
            await svc.stop()
    asyncio.run(run())


def test_engine_refusal_creates_error_session(make_service):
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "activate premium"})
    svc = make_service(handler=handler)

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert s.state == "error" and s.error == "engine_refused" and "premium" in s.error_message
            assert s.process is None
        finally:
            await svc.stop()
    asyncio.run(run())


def test_ffmpeg_missing(make_service):
    svc = make_service(ffmpeg=None)
    svc.ffmpeg_path = lambda: None  # type: ignore[method-assign]

    async def run():
        s = await svc.open_session(IH)
        assert s.state == "error" and s.error == "ffmpeg_missing"
    asyncio.run(run())


def test_ffmpeg_exit_before_ready_is_ffmpeg_failed(make_service):
    svc = make_service(mode="exit_early")

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert await _wait(lambda: s.state == "error")
            assert s.error == "ffmpeg_failed" and "Connection refused" in s.error_message
        finally:
            await svc.stop()
    asyncio.run(run())


def test_stall_after_start_timeout(make_service):
    svc = make_service(mode="never_ready", start_timeout=1)

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            svc._clock["now"] += 2
            await svc.tick()
            assert s.state == "error" and s.error == "engine_stalled"
            assert "peers" in s.error_message
        finally:
            await svc.stop()
    asyncio.run(run())


def test_flooded_stderr_keeps_session_ready(make_service):
    svc = make_service(mode="flood_stderr")

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert await _wait(lambda: svc.hls_ready(s))
            await asyncio.sleep(0.5)
            await svc.tick()
            assert s.state == "ready"
            assert len(s.stderr_tail) <= 20
        finally:
            await svc.stop()
    asyncio.run(run())


def test_reaper_rules(make_service):
    svc = make_service()

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            # idle regardless of viewers
            svc._clock["now"] += 21
            await svc.tick()
            assert s.state == "stopped" and svc.get(s.id) is None and not s.dir.exists()

            s2 = await svc.open_session(IH)
            svc.touch(s2.id)
            svc.leave(s2.id)
            svc._clock["now"] += 6
            await svc.tick()
            assert s2.state == "stopped"

            s3 = await svc.open_session(IH)
            svc.touch(s3.id)
            svc._clock["now"] += 3
            svc.touch(s3.id)  # status polls keep it alive
            await svc.tick()
            assert s3.state != "stopped"
        finally:
            await svc.stop()
    asyncio.run(run())


def test_error_sessions_are_reaped_after_a_minute(make_service):
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "nope"})
    svc = make_service(handler=handler)

    async def run():
        s = await svc.open_session(IH)
        svc.touch(s.id)
        svc._clock["now"] += 61
        await svc.tick()
        assert svc.get(s.id) is None
    asyncio.run(run())


def test_teardown_tolerates_exited_process_and_keeps_ticking(make_service, monkeypatch):
    svc = make_service(mode="exit_early")

    async def run():
        await svc.start()
        try:
            s = await svc.open_session(IH)
            assert await _wait(lambda: s.state == "error")
            s2 = await svc.open_session(IH2)
            # Make the first teardown raise inside rmtree; the second session must still be handled.
            import shutil
            real_rmtree = shutil.rmtree
            calls = {"n": 0}

            def flaky(path, ignore_errors=False):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise RuntimeError("boom")
                real_rmtree(path, ignore_errors=ignore_errors)
            monkeypatch.setattr(shutil, "rmtree", flaky)
            svc._clock["now"] += 61
            await svc.tick()
            svc._clock["now"] += 61
            await svc.tick()
            assert svc.get(s2.id) is None
        finally:
            monkeypatch.undo()
            await svc.stop()
    asyncio.run(run())


def test_startup_sweep_kills_only_our_ffmpeg(make_service, tmp_path):
    svc = make_service()
    hls = tmp_path / "hls"
    ours = hls / ("a" * 32)
    ours.mkdir(parents=True)
    foreign = hls / "keep-me"
    foreign.mkdir()
    (foreign / "note.txt").write_text("x")
    # A fake process whose cmdline contains our session dir.
    import subprocess
    proc = subprocess.Popen([sys.executable, "-c", f"import time; x={str(ours)!r}; time.sleep(60)"])
    (ours / "ffmpeg.pid").write_text(str(proc.pid))
    # A pid that is not ours (this test process).
    other = hls / ("b" * 32)
    other.mkdir()
    (other / "ffmpeg.pid").write_text(str(os.getpid()))

    async def run():
        await svc.start()
        await svc.stop()
    asyncio.run(run())
    assert proc.poll() is not None, "our stale ffmpeg must be killed"
    assert not ours.exists() and not other.exists()
    assert (foreign / "note.txt").exists()


def test_stop_tears_down_quickly(make_service):
    svc = make_service()

    async def run():
        await svc.start()
        s = await svc.open_session(IH)
        assert await _wait(lambda: svc.hls_ready(s))
        t0 = time.monotonic()
        await svc.stop()
        assert time.monotonic() - t0 < 3.0
        assert s.state == "stopped" and not s.dir.exists()
    asyncio.run(run())


def test_spawn_argv_contains_required_flags(make_service):
    svc = make_service()
    argv = svc.ffmpeg_argv("http://engine/content/x", Path("/tmp/x"))
    assert argv[:9] == [str(FAKE_FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "info", "-nostats", "-rw_timeout", "20000000", "-fflags"]
    assert "-c:a" in argv and argv[argv.index("-c:a") + 1] == "aac"
    assert argv[-1] == "/tmp/x/index.m3u8"
```

- [ ] **Step 2: Run to verify failure**

Run: `chmod +x backend/tests/fake_ffmpeg.py && PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_player_service.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement the service**

Create `backend/app/services/player_service.py`:

```python
"""Web player sessions: one shared ffmpeg (video copy, audio -> AAC, HLS) per
channel, an asyncio reaper/stat loop and a startup sweep (spec 5.1)."""
from __future__ import annotations

import asyncio
import contextlib
import ctypes
import logging
import os
import re
import shutil
import signal
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Deque, Dict, List, Literal, Optional

from fastapi.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.services.engine_client import (
    EngineClient, EngineRefusedError, EngineSession, EngineStats, EngineUnavailableError, engine_url_from_settings,
)

logger = logging.getLogger(__name__)

PlayerState = Literal["starting", "ready", "error", "stopped"]
PlayerError = Literal["engine_unavailable", "engine_refused", "engine_stalled", "ffmpeg_missing", "ffmpeg_failed"]

IDLE_SECONDS = 20.0
NO_VIEWERS_SECONDS = 5.0
ERROR_SECONDS = 60.0
TICK_SECONDS = 5.0
STDERR_TAIL = 20
_SESSION_DIR = re.compile(r"^[0-9a-f]{32}$")
_STREAM_LINE = re.compile(r"Stream #0:\d+.*?: (Video|Audio): ([A-Za-z0-9_]+)")


class PlayerLimitReached(RuntimeError):
    def __init__(self, limit: int, active: int):
        super().__init__(f"player session limit reached ({active}/{limit})")
        self.limit = limit
        self.active = active


@dataclass
class PlayerSession:
    id: str
    content_id: str
    dir: Path
    created_at: float
    last_access: float
    state: PlayerState = "starting"
    error: Optional[PlayerError] = None
    error_message: str = ""
    viewers: int = 0
    viewers_zero_since: Optional[float] = None
    engine_session: Optional[EngineSession] = None
    process: Optional[asyncio.subprocess.Process] = None
    codecs: Dict[str, Optional[str]] = field(default_factory=lambda: {"video": None, "audio": None})
    stats: Optional[EngineStats] = None
    stderr_tail: Deque[str] = field(default_factory=lambda: deque(maxlen=STDERR_TAIL))
    error_since: Optional[float] = None
    _reader: Optional[asyncio.Task] = None


def _set_pdeathsig() -> None:  # runs in the child between fork and exec (Linux only)
    if sys.platform.startswith("linux"):
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            libc.prctl(1, signal.SIGTERM)  # PR_SET_PDEATHSIG
        except Exception:  # noqa: BLE001
            pass


def _engine_from_settings() -> EngineClient:
    from app.config.database import SessionLocal
    from app.repositories.settings_repository import SettingsRepository

    db = SessionLocal()
    try:
        return EngineClient(engine_url_from_settings(SettingsRepository(db)))
    finally:
        db.close()


class PlayerService:
    def __init__(
        self,
        *,
        settings_getter: Callable = get_settings,
        engine_factory: Callable[[], EngineClient] = _engine_from_settings,
        ffmpeg_path: Optional[str] = None,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self._settings = settings_getter
        self._engine_factory = engine_factory
        self._ffmpeg_override = ffmpeg_path
        self._now = monotonic
        self.sessions: Dict[str, PlayerSession] = {}
        self._loop_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    # --- configuration -----------------------------------------------------
    def hls_dir(self) -> Path:
        return Path(self._settings().PLAYER_HLS_DIR)

    def ffmpeg_path(self) -> Optional[str]:
        if self._ffmpeg_override:
            return self._ffmpeg_override
        configured = (self._settings().FFMPEG_BINARY_PATH or "").strip()
        if configured and os.access(configured, os.X_OK):
            return configured
        return shutil.which("ffmpeg")

    def capabilities(self) -> dict:
        path = self.ffmpeg_path()
        return {
            "ffmpeg_available": path is not None,
            "ffmpeg_path": path,
            "max_sessions": int(self._settings().PLAYER_MAX_SESSIONS),
            "hls_dir": str(self.hls_dir()),
        }

    def ffmpeg_argv(self, playback_url: str, directory: Path) -> List[str]:
        return [
            str(self.ffmpeg_path()), "-nostdin", "-hide_banner", "-loglevel", "info", "-nostats",
            "-rw_timeout", "20000000", "-fflags", "+genpts+discardcorrupt",
            "-i", playback_url, "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
            "-f", "hls", "-hls_time", "2", "-hls_list_size", "6", "-hls_delete_threshold", "2",
            "-hls_flags", "delete_segments+independent_segments+omit_endlist+temp_file",
            "-hls_segment_type", "mpegts", "-hls_segment_filename", str(directory / "seg%05d.ts"),
            str(directory / "index.m3u8"),
        ]

    # --- lifecycle -----------------------------------------------------------
    async def start(self) -> None:
        self._sweep_stale_dirs()
        if self._loop_task is None:
            self._loop_task = asyncio.create_task(self._run_loop(), name="player-service-loop")
            self._loop_task.add_done_callback(self._on_loop_done)

    async def stop(self) -> None:
        if self._loop_task is not None:
            self._loop_task.remove_done_callback(self._on_loop_done)
            self._loop_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._loop_task
            self._loop_task = None
        for session in list(self.sessions.values()):
            await self._teardown(session, immediate=True)

    def _on_loop_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        logger.error("Player loop exited unexpectedly: %s; restarting", exc)
        self._loop_task = asyncio.create_task(self._run_loop(), name="player-service-loop")
        self._loop_task.add_done_callback(self._on_loop_done)

    async def _run_loop(self) -> None:
        while True:
            await asyncio.sleep(TICK_SECONDS)
            try:
                await self.tick()
            except Exception:  # noqa: BLE001
                logger.exception("Player tick failed")

    def _sweep_stale_dirs(self) -> None:
        root = self.hls_dir()
        if not root.is_dir():
            return
        for entry in root.iterdir():
            if not entry.is_dir() or not _SESSION_DIR.match(entry.name):
                continue
            pid_file = entry / "ffmpeg.pid"
            try:
                pid = int(pid_file.read_text().strip()) if pid_file.exists() else None
            except ValueError:
                pid = None
            if pid and _cmdline_mentions(pid, str(entry)):
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.kill(pid, signal.SIGKILL)
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline and _pid_alive(pid):
                    time.sleep(0.05)
            shutil.rmtree(entry, ignore_errors=True)

    # --- sessions ------------------------------------------------------------
    def list_sessions(self) -> List[PlayerSession]:
        return list(self.sessions.values())

    def get(self, session_id: str) -> Optional[PlayerSession]:
        return self.sessions.get(session_id)

    def touch(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is not None:
            session.last_access = self._now()

    def leave(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is None:
            return
        session.viewers = max(0, session.viewers - 1)
        if session.viewers == 0 and session.viewers_zero_since is None:
            session.viewers_zero_since = self._now()

    def playlist_path(self, session: PlayerSession) -> Path:
        return session.dir / "index.m3u8"

    def hls_ready(self, session: PlayerSession) -> bool:
        playlist = self.playlist_path(session)
        if not playlist.exists():
            return False
        try:
            lines = playlist.read_text().splitlines()
        except OSError:
            return False
        return sum(1 for line in lines if line.strip().endswith(".ts")) >= 2

    async def open_session(self, content_id: str) -> PlayerSession:
        async with self._lock:
            for existing in self.sessions.values():
                if existing.content_id == content_id and existing.state != "stopped":
                    existing.viewers += 1
                    existing.viewers_zero_since = None
                    existing.last_access = self._now()
                    return existing
            limit = int(self._settings().PLAYER_MAX_SESSIONS)
            active = sum(1 for s in self.sessions.values() if s.state in ("starting", "ready"))
            if active >= limit:
                raise PlayerLimitReached(limit, active)
            now = self._now()
            session = PlayerSession(id=uuid.uuid4().hex, content_id=content_id, dir=self.hls_dir() / uuid.uuid4().hex,
                                    created_at=now, last_access=now, viewers=1)
            session.dir = self.hls_dir() / session.id
            self.sessions[session.id] = session
        await self._launch(session)
        return session

    async def _launch(self, session: PlayerSession) -> None:
        ffmpeg = self.ffmpeg_path()
        if ffmpeg is None:
            self._fail(session, "ffmpeg_missing", "ffmpeg is not installed on this server")
            return
        try:
            engine = await run_in_threadpool(self._engine_factory)
            session.engine_session = await run_in_threadpool(engine.start, session.content_id)
        except EngineRefusedError as exc:
            self._fail(session, "engine_refused", str(exc))
            return
        except EngineUnavailableError as exc:
            self._fail(session, "engine_unavailable", str(exc))
            return
        session.dir.mkdir(parents=True, exist_ok=True)
        argv = self.ffmpeg_argv(session.engine_session.playback_url, session.dir)
        try:
            session.process = await asyncio.create_subprocess_exec(
                *argv, stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE, start_new_session=True, preexec_fn=_set_pdeathsig,
            )
        except OSError as exc:
            self._fail(session, "ffmpeg_failed", f"could not start ffmpeg: {exc}")
            return
        (session.dir / "ffmpeg.pid").write_text(str(session.process.pid))
        session._reader = asyncio.create_task(self._read_stderr(session), name=f"ffmpeg-stderr-{session.id[:8]}")

    def _fail(self, session: PlayerSession, error: PlayerError, message: str) -> None:
        if session.state == "stopped":
            return
        session.state = "error"
        session.error = error
        session.error_message = message
        session.error_since = self._now()

    async def _read_stderr(self, session: PlayerSession) -> None:
        proc = session.process
        assert proc is not None and proc.stderr is not None
        stream = proc.stderr
        try:
            while True:
                try:
                    raw = await stream.readline()
                except (asyncio.LimitOverrunError, ValueError):
                    raw = await stream.read(4096)
                if not raw:
                    break
                line = raw.decode("utf-8", "replace").replace("\r", "\n").strip()
                if not line:
                    continue
                session.stderr_tail.append(line[-300:])
                match = _STREAM_LINE.search(line)
                if match:
                    kind, codec = match.group(1).lower(), match.group(2).lower()
                    if session.codecs.get(kind) is None:
                        session.codecs[kind] = codec
        finally:
            with contextlib.suppress(Exception):
                await proc.wait()
            if session.state != "stopped":
                self._fail(session, "ffmpeg_failed", " | ".join(list(session.stderr_tail)[-5:]) or f"ffmpeg exited with {proc.returncode}")

    # --- periodic work -------------------------------------------------------
    async def tick(self) -> None:
        now = self._now()
        for session in list(self.sessions.values()):
            try:
                await self._tick_session(session, now)
            except Exception:  # noqa: BLE001
                logger.exception("Player session %s tick failed", session.id)

    async def _tick_session(self, session: PlayerSession, now: float) -> None:
        if session.state in ("starting", "ready") and session.engine_session is not None:
            try:
                engine = await run_in_threadpool(self._engine_factory)
                session.stats = await run_in_threadpool(engine.stat, session.engine_session)
            except Exception as exc:  # noqa: BLE001 - stats are best effort
                logger.warning("Player stats for %s unavailable: %s", session.content_id, exc)
        if session.state == "starting":
            if self.hls_ready(session):
                session.state = "ready"
            elif now - session.created_at > float(self._settings().PLAYER_START_TIMEOUT_SECONDS):
                stats = session.stats
                detail = f"{stats.peers} peers (status={stats.status})" if stats else "no engine statistics"
                self._fail(session, "engine_stalled", f"the stream did not start: {detail}")
        idle = now - session.last_access > IDLE_SECONDS
        no_viewers = session.viewers == 0 and session.viewers_zero_since is not None and now - session.viewers_zero_since > NO_VIEWERS_SECONDS
        errored = session.state == "error" and session.error_since is not None and now - session.error_since > ERROR_SECONDS
        if idle or no_viewers or errored:
            await self._teardown(session)

    async def _teardown(self, session: PlayerSession, immediate: bool = False) -> None:
        session.state = "stopped"
        proc = session.process
        if proc is not None and proc.returncode is None:
            try:
                pgid = os.getpgid(proc.pid)
            except ProcessLookupError:
                pgid = None
            with contextlib.suppress(ProcessLookupError):
                if pgid is not None:
                    os.killpg(pgid, signal.SIGKILL if immediate else signal.SIGTERM)
            if not immediate:
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        if pgid is not None:
                            os.killpg(pgid, signal.SIGKILL)
            with contextlib.suppress(Exception):
                await asyncio.wait_for(proc.wait(), timeout=2.0)
        if session._reader is not None:
            session._reader.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await session._reader
        if session.engine_session is not None:
            try:
                engine = await run_in_threadpool(self._engine_factory)
                await run_in_threadpool(engine.stop, session.engine_session)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Engine stop for %s failed: %s", session.content_id, exc)
        try:
            shutil.rmtree(session.dir, ignore_errors=True)
        except Exception:  # noqa: BLE001 - never let cleanup stop the loop
            logger.exception("Could not remove %s", session.dir)
        self.sessions.pop(session.id, None)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _cmdline_mentions(pid: int, needle: str) -> bool:
    proc_path = Path(f"/proc/{pid}/cmdline")
    try:
        if proc_path.exists():
            return needle in proc_path.read_bytes().decode("utf-8", "replace")
        import subprocess
        out = subprocess.run(["ps", "-o", "args=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
        return needle in out.stdout
    except Exception:  # noqa: BLE001
        return False


player_service = PlayerService()
```

Note on `test_teardown_tolerates_exited_process_and_keeps_ticking`: `shutil.rmtree(..., ignore_errors=True)` is wrapped in `try/except` so a raising monkeypatched `rmtree` still leaves the session removed from the registry; the second session is torn down on the same/next tick.

- [ ] **Step 4: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_player_service.py -x`
Expected: PASS. macOS note: `preexec_fn` + `start_new_session` work; PDEATHSIG is a no-op there.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/player_service.py backend/tests/fake_ffmpeg.py backend/tests/test_player_service.py
git commit -m "feat(player): session service with shared ffmpeg HLS pipeline, reaper and startup sweep"
```

---

### Task 4: Player endpoints and lifespan wiring

**Files:**
- Create: `backend/app/schemas/player.py`, `backend/app/api/endpoints/player.py`
- Modify: `backend/app/api/api.py`, `backend/main.py` (lifespan start/stop)
- Test: `backend/tests/test_player_endpoints.py`, `backend/tests/test_api_token_auth.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/player/sessions {content_id}` → 200 `PlayerSessionStatus`; 409 `PLAYER_LIMIT_REACHED` (`context.limit`, `context.active`); 422 on a non-40-hex id.
  - `GET /api/v1/player/sessions` → `PlayerSessionListResponse{sessions}`; `GET /sessions/{id}` → `PlayerSessionStatus` (touches); 404 when gone.
  - `GET /sessions/{id}/index.m3u8` (token propagation), `GET /sessions/{id}/{segment}` (`^seg\d{5}\.ts$`), `DELETE /sessions/{id}` → 204, `GET /capabilities` → `PlayerCapabilities`.
  - DTOs: `PlayerSessionCreate{content_id}`, `PlayerCodecs{video,audio}`, `PlayerStats{status,peers,speed_down,speed_up}`, `PlayerSessionStatus{id,content_id,state,error,error_message,codecs,stats,viewers,playlist_url,hls_ready}`, `PlayerSessionListResponse`, `PlayerCapabilities{ffmpeg_available,ffmpeg_path,max_sessions,hls_dir}`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_player_endpoints.py`:

```python
"""/api/v1/player: session create/status/delete, HLS files, token propagation (spec 5.1, 4.4)."""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from app.services.engine_client import EngineClient
from app.services.player_service import PlayerService

FAKE_FFMPEG = Path(__file__).parent / "fake_ffmpeg.py"
IH = "0" * 40
TOKEN = "s3cret"


def _engine():
    def handler(request):
        if request.url.path == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        return httpx.Response(200, json={"response": {"status": "dl", "peers": 1, "speed_down": 1, "speed_up": 0}, "error": None})
    return EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler)))


class _Settings:
    def __init__(self, hls_dir):
        self.PLAYER_HLS_DIR = str(hls_dir)
        self.PLAYER_MAX_SESSIONS = 1
        self.PLAYER_START_TIMEOUT_SECONDS = 45
        self.FFMPEG_BINARY_PATH = ""


@pytest.fixture
def player(tmp_path, monkeypatch):
    import app.api.endpoints.player as endpoint
    svc = PlayerService(settings_getter=lambda: _Settings(tmp_path / "hls"), engine_factory=_engine, ffmpeg_path=str(FAKE_FFMPEG))
    monkeypatch.setattr(endpoint, "player_service", svc)
    yield svc
    asyncio.run(svc.stop())


def _wait_ready(client, session_id, tries=60):
    for _ in range(tries):
        body = client.get(f"/api/v1/player/sessions/{session_id}").json()
        if body["hls_ready"]:
            return body
        import time; time.sleep(0.05)
    raise AssertionError("session never became ready")


def test_create_status_playlist_segment_delete(client, player):
    created = client.post("/api/v1/player/sessions", json={"content_id": IH})
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["state"] == "starting" and body["content_id"] == IH and body["viewers"] == 1
    assert body["playlist_url"] == f"/api/v1/player/sessions/{body['id']}/index.m3u8"
    ready = _wait_ready(client, body["id"])
    assert ready["codecs"] == {"video": "h264", "audio": "ac3"}

    playlist = client.get(ready["playlist_url"])
    assert playlist.status_code == 200
    assert playlist.headers["content-type"].startswith("application/vnd.apple.mpegurl")
    assert playlist.headers["cache-control"] == "no-store"
    lines = [l for l in playlist.text.splitlines() if l and not l.startswith("#")]
    assert lines and all(l.endswith(".ts") for l in lines)
    segment = client.get(f"/api/v1/player/sessions/{body['id']}/{lines[0]}")
    assert segment.status_code == 200 and segment.headers["content-type"] == "video/mp2t"

    assert client.get(f"/api/v1/player/sessions/{body['id']}/../etc").status_code in (404, 422)
    assert client.get(f"/api/v1/player/sessions/{body['id']}/evil.ts").status_code == 404
    assert client.delete(f"/api/v1/player/sessions/{body['id']}").status_code == 204
    assert client.get(f"/api/v1/player/sessions/{body['id']}").json()["viewers"] == 0
    listing = client.get("/api/v1/player/sessions").json()
    assert [s["id"] for s in listing["sessions"]] == [body["id"]]


def test_join_existing_session(client, player):
    first = client.post("/api/v1/player/sessions", json={"content_id": IH}).json()
    second = client.post("/api/v1/player/sessions", json={"content_id": IH}).json()
    assert second["id"] == first["id"] and second["viewers"] == 2


def test_limit_reached_envelope(client, player):
    client.post("/api/v1/player/sessions", json={"content_id": IH})
    response = client.post("/api/v1/player/sessions", json={"content_id": "1" * 40})
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "PLAYER_LIMIT_REACHED" and error["context"] == {"limit": 1, "active": 1}


def test_invalid_content_id(client, player):
    assert client.post("/api/v1/player/sessions", json={"content_id": "nope"}).status_code == 422


def test_unknown_session_404(client, player):
    assert client.get("/api/v1/player/sessions/" + "f" * 32).status_code == 404
    assert client.get("/api/v1/player/sessions/" + "f" * 32 + "/index.m3u8").status_code == 404


def test_capabilities(client, player):
    body = client.get("/api/v1/player/capabilities").json()
    assert body["ffmpeg_available"] is True and body["ffmpeg_path"] == str(FAKE_FFMPEG)
    assert body["max_sessions"] == 1 and body["hls_dir"].endswith("hls")


def test_playlist_propagates_query_token_for_native_players(client, player, monkeypatch):
    monkeypatch.setenv("API_TOKEN", TOKEN)
    created = client.post(f"/api/v1/player/sessions?token={TOKEN}", json={"content_id": IH}).json()
    ready = _wait_ready_with_token(client, created["id"])
    by_query = client.get(f"{ready['playlist_url']}?token={TOKEN}")
    assert by_query.status_code == 200
    uris = [l for l in by_query.text.splitlines() if l and not l.startswith("#")]
    assert uris and all(l.endswith(f"?token={TOKEN}") for l in uris)
    assert all(l.startswith("#") or l.endswith(f"?token={TOKEN}") for l in by_query.text.splitlines() if l)
    # Each rewritten URI resolves and is accepted; the same segment without a token is 401.
    seg = uris[0]
    assert client.get(f"/api/v1/player/sessions/{created['id']}/{seg}").status_code == 200
    assert client.get(f"/api/v1/player/sessions/{created['id']}/{seg.split('?')[0]}").status_code == 401
    by_header = client.get(ready["playlist_url"], headers={"X-Api-Token": TOKEN})
    assert by_header.text == (player.get(created["id"]).dir / "index.m3u8").read_text()
    assert client.delete(f"/api/v1/player/sessions/{created['id']}?token={TOKEN}").status_code == 204


def test_reserved_characters_in_token_are_encoded(client, player, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "a b&c")
    created = client.post("/api/v1/player/sessions", json={"content_id": IH}, headers={"X-Api-Token": "a b&c"}).json()
    ready = _wait_ready_with_token(client, created["id"], token="a b&c")
    text = client.get(ready["playlist_url"], params={"token": "a b&c"}).text
    assert "seg00000.ts?token=a+b%26c" in text or "?token=a+b%26c" in text


def _wait_ready_with_token(client, session_id, token=TOKEN, tries=60):
    for _ in range(tries):
        body = client.get(f"/api/v1/player/sessions/{session_id}", headers={"X-Api-Token": token}).json()
        if body["hls_ready"]:
            return body
        import time; time.sleep(0.05)
    raise AssertionError("session never became ready")
```

Append to `backend/tests/test_api_token_auth.py` `TestTokenEnforced`:

```python
    def test_player_routes_require_token(self, client, token_enabled):
        assert client.get("/api/v1/player/capabilities").status_code == 401
        assert client.get(f"/api/v1/player/capabilities?token={TOKEN}").status_code == 200
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_player_endpoints.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Schemas**

Create `backend/app/schemas/player.py`:

```python
"""DTOs for the web player (/api/v1/player)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

PlayerStateValue = Literal["starting", "ready", "error", "stopped"]
PlayerErrorValue = Literal["engine_unavailable", "engine_refused", "engine_stalled", "ffmpeg_missing", "ffmpeg_failed"]


class PlayerSessionCreate(BaseModel):
    content_id: str = Field(..., pattern=r"^[0-9a-fA-F]{40}$", description="AceStream content id (40 hex)")


class PlayerCodecs(BaseModel):
    video: Optional[str] = None
    audio: Optional[str] = None


class PlayerStats(BaseModel):
    status: str
    peers: int
    speed_down: int
    speed_up: int


class PlayerSessionStatus(BaseModel):
    id: str
    content_id: str
    state: PlayerStateValue
    error: Optional[PlayerErrorValue] = None
    error_message: str = ""
    codecs: PlayerCodecs
    stats: Optional[PlayerStats] = None
    viewers: int
    playlist_url: str
    hls_ready: bool


class PlayerSessionListResponse(BaseModel):
    sessions: List[PlayerSessionStatus]


class PlayerCapabilities(BaseModel):
    ffmpeg_available: bool
    ffmpeg_path: Optional[str] = None
    max_sessions: int
    hls_dir: str
```

- [ ] **Step 4: Endpoints**

Create `backend/app/api/endpoints/player.py`:

```python
"""Web player sessions (spec 5.1). Session create runs its blocking work in
the threadpool; HLS file handlers are async and touch no DB."""
from __future__ import annotations

import re
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse

from app.api.error_handlers import APIError
from app.schemas.player import (
    PlayerCapabilities, PlayerCodecs, PlayerSessionCreate, PlayerSessionListResponse, PlayerSessionStatus, PlayerStats,
)
from app.services.player_service import PlayerLimitReached, PlayerSession, player_service

router = APIRouter(tags=["player"])
_SEGMENT = re.compile(r"^seg\d{5}\.ts$")


def _status(session: PlayerSession) -> PlayerSessionStatus:
    stats = session.stats
    return PlayerSessionStatus(
        id=session.id, content_id=session.content_id, state=session.state, error=session.error,
        error_message=session.error_message, codecs=PlayerCodecs(**session.codecs),
        stats=PlayerStats(status=stats.status, peers=stats.peers, speed_down=stats.speed_down, speed_up=stats.speed_up) if stats else None,
        viewers=session.viewers, playlist_url=f"/api/v1/player/sessions/{session.id}/index.m3u8",
        hls_ready=player_service.hls_ready(session),
    )


def _session_or_404(session_id: str) -> PlayerSession:
    session = player_service.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player session not found")
    return session


@router.get("/capabilities", response_model=PlayerCapabilities, summary="Whether the server can prepare streams for browsers")
async def capabilities():
    return player_service.capabilities()


@router.get("/sessions", response_model=PlayerSessionListResponse, summary="Active player sessions")
async def list_sessions():
    return PlayerSessionListResponse(sessions=[_status(s) for s in player_service.list_sessions()])


@router.post("/sessions", response_model=PlayerSessionStatus, summary="Start (or join) playback of a channel")
async def create_session(payload: PlayerSessionCreate):
    try:
        session = await player_service.open_session(payload.content_id.lower())
    except PlayerLimitReached as exc:
        raise APIError(code="PLAYER_LIMIT_REACHED", message="Too many channels are playing at once",
                       status_code=status.HTTP_409_CONFLICT, context={"limit": exc.limit, "active": exc.active}) from exc
    return _status(session)


@router.get("/sessions/{session_id}", response_model=PlayerSessionStatus, summary="Session status (heartbeat)")
async def get_session(session_id: str):
    session = _session_or_404(session_id)
    player_service.touch(session_id)
    return _status(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Leave a session")
async def leave_session(session_id: str):
    player_service.leave(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions/{session_id}/index.m3u8", summary="HLS playlist", response_class=Response)
async def playlist(session_id: str, request: Request):
    session = _session_or_404(session_id)
    player_service.touch(session_id)
    path = player_service.playlist_path(session)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not ready")
    text = path.read_text()
    # Native (Safari/iOS) players cannot send headers and drop the playlist's
    # query when resolving relative segment URIs: carry ?token= onto each one.
    token = request.query_params.get("token")
    if token:
        suffix = "?" + urlencode({"token": token})
        text = "\n".join(line + suffix if line and not line.startswith("#") else line for line in text.splitlines()) + "\n"
    return Response(content=text, media_type="application/vnd.apple.mpegurl", headers={"Cache-Control": "no-store"})


@router.get("/sessions/{session_id}/{segment}", summary="HLS segment", response_class=FileResponse)
async def segment(session_id: str, segment: str):
    session = _session_or_404(session_id)
    if not _SEGMENT.match(segment):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown segment")
    player_service.touch(session_id)
    path = session.dir / segment
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not ready")
    return FileResponse(path, media_type="video/mp2t", headers={"Cache-Control": "no-store"})
```

`backend/app/api/api.py`: import `player` and add `api_router.include_router(player.router, prefix="/player", tags=["player"])`.

`backend/main.py` lifespan: after `_schedule_deferred_migration()` add `await player_service.start()` (import `from app.services.player_service import player_service`), and in the `finally` block, before `task_service.shutdown()`, `await player_service.stop()`.

- [ ] **Step 5: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_player_endpoints.py backend/tests/test_api_token_auth.py backend/tests/test_error_contracts.py`
Expected: PASS. (`client` does not enter the lifespan, so `player_service.start()` is not invoked; the fixture's service has no loop — the tests poll status, which computes `hls_ready` on demand.)

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/player.py backend/app/api/endpoints/player.py backend/app/api/api.py backend/main.py backend/tests/test_player_endpoints.py backend/tests/test_api_token_auth.py
git commit -m "feat(player): session, HLS and capabilities endpoints with token propagation"
```

---

### Task 5: Frontend player service, hooks and `StreamPlayerDialog`

**Files:**
- Modify: `frontend/package.json` (+ `hls.js`), `frontend/vite.config.ts` (chunk), `frontend/src/__tests__/viteConfig.test.ts`
- Create: `frontend/src/services/playerService.ts`, `frontend/src/hooks/usePlayer.ts`, `frontend/src/components/player/StreamPlayerDialog.tsx`, `frontend/src/components/player/playerCopy.ts`
- Test: `frontend/src/__tests__/playerService.test.ts`, `frontend/src/__tests__/StreamPlayerDialog.test.tsx`

**Interfaces:**
- Produces: `playerService.{getCapabilities, startSession(contentId), getSession(id), leaveSession(id, token?)}`; hooks `usePlayerCapabilities()`, `useStartPlayerSession()`, `usePlayerSessionStatus(id | null)` (2 s while starting, 10 s while ready, stops on error/404); `StreamPlayerDialog` props `{ open: boolean; contentId: string | null; title: string; onClose: () => void; extraActions?: React.ReactNode }` (plan 3 injects "Play on…" through `extraActions`); `describePlayerError(status, hlsCodecError) -> string | null` in `playerCopy.ts`.

- [ ] **Step 1: Install and write the failing tests**

```bash
cd frontend && npm install hls.js@^1.7.2 && cd ..
```

`frontend/src/__tests__/viteConfig.test.ts` — add `expect(configSource).toContain("return 'player-vendor'");` and `expect(configSource).toContain("id.includes('node_modules/hls.js')");`.

Create `frontend/src/__tests__/playerService.test.ts`:

```ts
import apiClient from '../services/apiClient';
import { playerService } from '../services/playerService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), delete: jest.fn() },
}));

describe('playerService', () => {
  beforeEach(() => jest.clearAllMocks());

  it('starts a session', async () => {
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { id: 's1', state: 'starting' } });
    await expect(playerService.startSession('a'.repeat(40))).resolves.toEqual({ id: 's1', state: 'starting' });
    expect(apiClient.post).toHaveBeenCalledWith('/v1/player/sessions', { content_id: 'a'.repeat(40) });
  });

  it('reads status and capabilities', async () => {
    (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { id: 's1' } }).mockResolvedValueOnce({ data: { ffmpeg_available: true } });
    await playerService.getSession('s1');
    await playerService.getCapabilities();
    expect(apiClient.get).toHaveBeenNthCalledWith(1, '/v1/player/sessions/s1');
    expect(apiClient.get).toHaveBeenNthCalledWith(2, '/v1/player/capabilities');
  });

  it('leaves with a keepalive DELETE that carries the token', async () => {
    const fetchMock = jest.fn().mockResolvedValue({ ok: true });
    (global as unknown as { fetch: jest.Mock }).fetch = fetchMock;
    window.localStorage.setItem('apiToken', 't k');
    playerService.leaveSession('s1');
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/player/sessions/s1?token=t+k', { method: 'DELETE', keepalive: true });
    window.localStorage.removeItem('apiToken');
  });
});
```

Create `frontend/src/__tests__/StreamPlayerDialog.test.tsx`:

```tsx
import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { act, fireEvent, render, screen } from '@testing-library/react';
import StreamPlayerDialog from '../components/player/StreamPlayerDialog';
import { describePlayerError } from '../components/player/playerCopy';
import { createAppTheme } from '../theme';

const mockStart = jest.fn();
const mockStatus = jest.fn();
const mockPublicUrl = jest.fn();
const mockLeave = jest.fn();
const hlsInstances: Array<{ loadSource: jest.Mock; attachMedia: jest.Mock; destroy: jest.Mock; on: jest.Mock }> = [];

jest.mock('hls.js', () => {
  class MockHls {
    static isSupported = () => true;
    static Events = { ERROR: 'hlsError' };
    static ErrorDetails = { BUFFER_INCOMPATIBLE_CODECS_ERROR: 'bufferIncompatibleCodecsError' };
    loadSource = jest.fn();
    attachMedia = jest.fn();
    destroy = jest.fn();
    on = jest.fn();
    constructor() { hlsInstances.push(this); }
  }
  return { __esModule: true, default: MockHls };
});
jest.mock('../hooks/usePlayer', () => ({
  useStartPlayerSession: () => ({ mutate: mockStart, isPending: false }),
  usePlayerSessionStatus: (id: string | null) => mockStatus(id),
}));
jest.mock('../hooks/useSystemServices', () => ({ usePublicUrl: () => mockPublicUrl() }));
jest.mock('../services/playerService', () => ({ playerService: { leaveSession: (...args: unknown[]) => mockLeave(...args) } }));

const renderDialog = (props: Partial<React.ComponentProps<typeof StreamPlayerDialog>> = {}) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <StreamPlayerDialog open contentId={'a'.repeat(40)} title="Arena TV" onClose={jest.fn()} {...props} />
    </ThemeProvider>
  );

describe('StreamPlayerDialog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    hlsInstances.length = 0;
    mockPublicUrl.mockReturnValue({ data: { url: 'http://scraper.lan:8000', source: 'setting', warnings: [] } });
    mockStart.mockImplementation((_id: string, opts: { onSuccess: (s: { id: string }) => void }) => opts.onSuccess({ id: 's1' }));
  });

  it('starts a session on open, shows starting stats, then attaches hls.js when ready', () => {
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'starting', hls_ready: false, stats: { peers: 4, speed_down: 900, speed_up: 0, status: 'prebuf' }, codecs: {}, playlist_url: '/api/v1/player/sessions/s1/index.m3u8', viewers: 1, error: null, error_message: '' } });
    const { rerender } = renderDialog();
    expect(mockStart).toHaveBeenCalledWith('a'.repeat(40), expect.any(Object));
    expect(screen.getByRole('status')).toHaveTextContent(/Starting.*4 peers/);
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'ready', hls_ready: true, stats: null, codecs: { video: 'h264', audio: 'ac3' }, playlist_url: '/api/v1/player/sessions/s1/index.m3u8', viewers: 1, error: null, error_message: '' } });
    rerender(
      <ThemeProvider theme={createAppTheme('light')}>
        <StreamPlayerDialog open contentId={'a'.repeat(40)} title="Arena TV" onClose={jest.fn()} />
      </ThemeProvider>
    );
    expect(hlsInstances).toHaveLength(1);
    expect(hlsInstances[0].loadSource).toHaveBeenCalledWith('/api/v1/player/sessions/s1/index.m3u8');
  });

  it('explains errors in plain language and offers the stream link', () => {
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'error', error: 'engine_stalled', error_message: 'no peers', hls_ready: false, stats: null, codecs: {}, playlist_url: '', viewers: 1 } });
    renderDialog();
    expect(screen.getByRole('alert')).toHaveTextContent('No one is sharing this channel right now');
    expect(screen.getByRole('button', { name: 'Copy stream link' })).toBeInTheDocument();
  });

  it('leaves the session with a keepalive DELETE on close and on pagehide', () => {
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'ready', hls_ready: true, stats: null, codecs: {}, playlist_url: '/p', viewers: 1, error: null, error_message: '' } });
    const onClose = jest.fn();
    renderDialog({ onClose });
    act(() => { window.dispatchEvent(new Event('pagehide')); });
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(mockLeave).toHaveBeenCalledTimes(1);
    expect(mockLeave).toHaveBeenCalledWith('s1');
    expect(onClose).toHaveBeenCalled();
  });
});

describe('describePlayerError', () => {
  it('maps codes to copy', () => {
    expect(describePlayerError({ error: 'ffmpeg_missing', error_message: '', codecs: {} }, false)).toMatch(/can't prepare streams/);
    expect(describePlayerError({ error: null, error_message: '', codecs: { video: 'mpeg2video' } }, false)).toMatch(/MPEG-2/);
    expect(describePlayerError({ error: null, error_message: '', codecs: {} }, true)).toMatch(/video format/);
    expect(describePlayerError({ error: 'engine_refused', error_message: 'activate premium', codecs: {} }, false)).toContain('activate premium');
    expect(describePlayerError({ error: null, error_message: '', codecs: { video: 'h264' } }, false)).toBeNull();
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npm test -- playerService.test.ts StreamPlayerDialog.test.tsx viteConfig.test.ts`
Expected: FAIL (modules missing).

- [ ] **Step 3: Implement**

`frontend/vite.config.ts` — add before the `@mui/x-data-grid` rule:

```ts
          if (id.includes('node_modules/hls.js')) {
            return 'player-vendor';
          }
```

`frontend/src/services/playerService.ts`:

```ts
import apiClient from './apiClient';
import { getApiBaseUrl } from '../config/runtime';
import { getApiToken } from './apiToken';

export type PlayerState = 'starting' | 'ready' | 'error' | 'stopped';
export type PlayerError = 'engine_unavailable' | 'engine_refused' | 'engine_stalled' | 'ffmpeg_missing' | 'ffmpeg_failed';

export interface PlayerCodecs {
  video?: string | null;
  audio?: string | null;
}

export interface PlayerStats {
  status: string;
  peers: number;
  speed_down: number;
  speed_up: number;
}

export interface PlayerSessionStatus {
  id: string;
  content_id: string;
  state: PlayerState;
  error: PlayerError | null;
  error_message: string;
  codecs: PlayerCodecs;
  stats: PlayerStats | null;
  viewers: number;
  playlist_url: string;
  hls_ready: boolean;
}

export interface PlayerCapabilities {
  ffmpeg_available: boolean;
  ffmpeg_path: string | null;
  max_sessions: number;
  hls_dir: string;
}

const BASE_URL = '/v1/player';

export const playerService = {
  getCapabilities: async (): Promise<PlayerCapabilities> => {
    const { data } = await apiClient.get<PlayerCapabilities>(`${BASE_URL}/capabilities`);
    return data;
  },
  startSession: async (contentId: string): Promise<PlayerSessionStatus> => {
    const { data } = await apiClient.post<PlayerSessionStatus>(`${BASE_URL}/sessions`, { content_id: contentId });
    return data;
  },
  getSession: async (id: string): Promise<PlayerSessionStatus> => {
    const { data } = await apiClient.get<PlayerSessionStatus>(`${BASE_URL}/sessions/${id}`);
    return data;
  },
  /** Fire-and-forget release; keepalive lets it complete during pagehide. sendBeacon is POST-only and cannot carry the token. */
  leaveSession: (id: string): void => {
    const token = getApiToken();
    const query = token ? `?${new URLSearchParams({ token }).toString()}` : '';
    const url = `${getApiBaseUrl({ dev: process.env.NODE_ENV === 'development' })}${BASE_URL}/sessions/${id}${query}`;
    try {
      void fetch(url, { method: 'DELETE', keepalive: true });
    } catch {
      // Best effort: the backend reaps idle sessions anyway.
    }
  },
};
```

`frontend/src/hooks/usePlayer.ts`:

```ts
import { useMutation, useQuery } from '@tanstack/react-query';
import { playerService, type PlayerCapabilities, type PlayerSessionStatus } from '../services/playerService';
import { ApiError } from '../services/apiErrors';

export const PLAYER_CAPABILITIES_QUERY_KEY = ['player', 'capabilities'] as const;
export const playerSessionKey = (id: string) => ['player', 'session', id] as const;

export const usePlayerCapabilities = () =>
  useQuery<PlayerCapabilities>({ queryKey: PLAYER_CAPABILITIES_QUERY_KEY, queryFn: playerService.getCapabilities, staleTime: 60_000 });

export const useStartPlayerSession = () =>
  useMutation<PlayerSessionStatus, ApiError, string>({ mutationFn: (contentId) => playerService.startSession(contentId) });

/** Polls the session: 2 s while starting (also the heartbeat), 10 s while ready, stops on error or once the session is gone. */
export const usePlayerSessionStatus = (id: string | null) =>
  useQuery<PlayerSessionStatus, ApiError>({
    queryKey: playerSessionKey(id ?? ''),
    queryFn: () => playerService.getSession(id as string),
    enabled: Boolean(id),
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data;
      const error = query.state.error;
      if (error || !status || status.state === 'error' || status.state === 'stopped') return false;
      return status.state === 'ready' ? 10_000 : 2_000;
    },
  });
```

`frontend/src/components/player/playerCopy.ts`:

```ts
import type { PlayerCodecs, PlayerError } from '../../services/playerService';

export interface PlayerErrorInput {
  error: PlayerError | null;
  error_message: string;
  codecs: PlayerCodecs;
}

const UNPLAYABLE_VIDEO = new Set(['mpeg2video', 'mpeg1video', 'vc1', 'msmpeg4v3']);

/** Plain-language explanation for the player status strip; null when nothing is wrong. */
export const describePlayerError = (status: PlayerErrorInput, hlsCodecError: boolean): string | null => {
  switch (status.error) {
    case 'ffmpeg_missing':
      return "This server can't prepare streams for the browser. Open the channel in VLC instead.";
    case 'engine_stalled':
      return 'No one is sharing this channel right now. Try again later or pick another stream.';
    case 'ffmpeg_failed':
      return 'The stream stopped unexpectedly. Try again.';
    case 'engine_refused':
    case 'engine_unavailable':
      return `The AceStream engine could not start this channel: ${status.error_message || 'no details'}.`;
    default:
      break;
  }
  const video = (status.codecs.video ?? '').toLowerCase();
  if (UNPLAYABLE_VIDEO.has(video)) {
    return "Your browser can't play this channel's video format (MPEG-2). Send it to VLC or Kodi instead.";
  }
  if (hlsCodecError) {
    return "Your browser can't play this channel's video format. Send it to VLC or Kodi instead.";
  }
  return null;
};
```

`frontend/src/components/player/StreamPlayerDialog.tsx`:

```tsx
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Snackbar, Stack, Typography, useMediaQuery, useTheme } from '@mui/material';
import Hls from 'hls.js';
import { usePlayerSessionStatus, useStartPlayerSession } from '../../hooks/usePlayer';
import { usePublicUrl } from '../../hooks/useSystemServices';
import { playerService } from '../../services/playerService';
import { getApiToken } from '../../services/apiToken';
import { buildPublicUrl } from '../../services/playlistService';
import { getErrorMessage } from '../../utils/errorUtils';
import { formatBitrate } from '../../utils/format';
import { describePlayerError } from './playerCopy';

export interface StreamPlayerDialogProps {
  open: boolean;
  contentId: string | null;
  title: string;
  onClose: () => void;
  /** Extra buttons (e.g. "Play on…") rendered next to Copy stream link. */
  extraActions?: React.ReactNode;
}

const withToken = (url: string): string => {
  const token = getApiToken();
  if (!token) return url;
  return `${url}${url.includes('?') ? '&' : '?'}${new URLSearchParams({ token }).toString()}`;
};

/** Plays one channel through the backend's HLS pipeline. */
const StreamPlayerDialog: React.FC<StreamPlayerDialogProps> = ({ open, contentId, title, onClose, extraActions }) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  const attachedUrl = useRef<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const [hlsCodecError, setHlsCodecError] = useState(false);
  const [copied, setCopied] = useState<'ok' | 'failed' | null>(null);
  const leftRef = useRef(false);

  const start = useStartPlayerSession();
  const { data: status, error: statusError } = usePlayerSessionStatus(sessionId);
  const { data: publicUrl } = usePublicUrl();

  const leave = useCallback(() => {
    if (leftRef.current || !sessionId) return;
    leftRef.current = true;
    playerService.leaveSession(sessionId);
  }, [sessionId]);

  const startSession = useCallback(() => {
    if (!contentId) return;
    setStartError(null);
    setHlsCodecError(false);
    leftRef.current = false;
    start.mutate(contentId, {
      onSuccess: (session) => setSessionId(session.id),
      onError: (err) => {
        if (err.code === 'PLAYER_LIMIT_REACHED') {
          const limit = (err.context as { limit?: number } | undefined)?.limit;
          setStartError(`Too many channels are playing at once${limit ? ` (limit ${limit})` : ''}. Close another player and try again.`);
        } else {
          setStartError(getErrorMessage(err));
        }
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentId]);

  useEffect(() => {
    if (open && contentId) startSession();
    return () => {
      leave();
      hlsRef.current?.destroy();
      hlsRef.current = null;
      attachedUrl.current = null;
      setSessionId(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, contentId]);

  useEffect(() => {
    const onPageHide = () => leave();
    window.addEventListener('pagehide', onPageHide);
    return () => window.removeEventListener('pagehide', onPageHide);
  }, [leave]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !status || !status.hls_ready || attachedUrl.current === status.playlist_url) return;
    attachedUrl.current = status.playlist_url;
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        liveSyncDurationCount: 3,
        xhrSetup: (xhr) => {
          const token = getApiToken();
          if (token) xhr.setRequestHeader('X-Api-Token', token);
        },
      });
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.details === Hls.ErrorDetails.BUFFER_INCOMPATIBLE_CODECS_ERROR || data.details === Hls.ErrorDetails.BUFFER_ADD_CODEC_ERROR) {
          setHlsCodecError(true);
        }
      });
      hls.loadSource(status.playlist_url);
      hls.attachMedia(video);
      hlsRef.current = hls;
    } else {
      video.src = withToken(status.playlist_url);
    }
    void video.play().catch(() => {
      video.muted = true;
      void video.play().catch(() => undefined);
    });
  }, [status]);

  const streamLink = contentId ? buildPublicUrl(`/tuner/stream/${contentId}.ts`, publicUrl?.url) : '';
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(streamLink);
      setCopied('ok');
    } catch {
      setCopied('failed');
    }
  };

  const gone = Boolean(statusError && statusError.status === 404);
  const problem = startError ?? (gone ? 'The stream ended.' : status ? describePlayerError(status, hlsCodecError) : null);
  const stats = status?.stats;
  const statusText = status?.state === 'ready'
    ? 'Playing'
    : status?.state === 'starting'
      ? `Starting… ${stats ? `${stats.peers} peers · ${formatBitrate(stats.speed_down * 8)}` : 'contacting the engine'}`
      : start.isPending
        ? 'Starting…'
        : '';

  return (
    <Dialog open={open} onClose={() => { leave(); onClose(); }} fullScreen={fullScreen} maxWidth="md" fullWidth aria-labelledby="stream-player-title">
      <DialogTitle id="stream-player-title">{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5}>
          <Box sx={{ position: 'relative', width: '100%', aspectRatio: '16 / 9', backgroundColor: '#000', borderRadius: 1, overflow: 'hidden' }}>
            <video ref={videoRef} controls autoPlay playsInline style={{ width: '100%', height: '100%' }} aria-label={`Video player for ${title}`} />
          </Box>
          {problem ? (
            <Alert severity={status?.error === 'ffmpeg_missing' ? 'warning' : 'error'} action={status?.error && status.error !== 'ffmpeg_missing' ? <Button color="inherit" size="small" onClick={startSession}>Retry</Button> : undefined}>
              {problem}
            </Alert>
          ) : (
            <Typography role="status" aria-live="polite" variant="body2" color="text.secondary">{statusText}</Typography>
          )}
          {status?.codecs.video ? (
            <Typography variant="caption" color="text.secondary">
              Video {status.codecs.video.toUpperCase()} · audio {(status.codecs.audio ?? 'unknown').toUpperCase()} re-encoded to AAC
            </Typography>
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        {extraActions}
        <Button onClick={handleCopy} disabled={!streamLink}>Copy stream link</Button>
        <Button variant="contained" onClick={() => { leave(); onClose(); }}>Close</Button>
      </DialogActions>
      <Snackbar open={copied !== null} autoHideDuration={3000} onClose={() => setCopied(null)}>
        <Alert severity={copied === 'ok' ? 'success' : 'error'} onClose={() => setCopied(null)}>
          {copied === 'ok' ? 'Stream link copied. Open it in VLC or any player on this network.' : 'Unable to copy the link.'}
        </Alert>
      </Snackbar>
    </Dialog>
  );
};

export default StreamPlayerDialog;
```

Notes: `ApiError` exposes `code`, `context` and `status` (see `services/apiErrors.ts`); `formatBitrate` takes bits per second (check its signature in `utils/format.ts` and adapt the multiplier if it expects kbit/s — the engine reports KB/s).

- [ ] **Step 4: Run the tests and checks**

Run: `cd frontend && npm test -- playerService.test.ts StreamPlayerDialog.test.tsx viteConfig.test.ts && npm run lint -- --max-warnings=0 && npm run typecheck`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts frontend/src/services/playerService.ts frontend/src/hooks/usePlayer.ts frontend/src/components/player frontend/src/__tests__/playerService.test.ts frontend/src/__tests__/StreamPlayerDialog.test.tsx frontend/src/__tests__/viteConfig.test.ts
git commit -m "feat(frontend): hls.js stream player dialog and player hooks"
```

---

### Task 6: Play action on the Acestream Channels rows (and e2e page object)

**Files:**
- Modify: `frontend/src/components/channels/ChannelRowActions.tsx`, `frontend/src/components/ChannelTable.tsx:141`, `frontend/src/pages/AcestreamChannels.tsx`
- Modify tests: `frontend/src/__tests__/ChannelTable.test.tsx`, `frontend/src/__tests__/ChannelCardList.test.tsx`, `frontend/src/__tests__/AcestreamChannelsPage.test.tsx`
- Create: `frontend/src/__tests__/ChannelRowActions.test.tsx`
- Modify: `e2e/src/pages/channels.ts`, `e2e/tests/07-tv-channels.spec.ts`

**Interfaces:**
- Produces: `ChannelActionHandlers.onPlay(channel)`; visible buttons `play channel ${name}` and `check channel status ${name}`; menu items `Link to a TV channel` / `Open TV channel: ${linkedName}`; page object `ChannelsPage.playChannel(name)`, `expectLinkedTv(name, tvName)`.

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/__tests__/ChannelRowActions.test.tsx`:

```tsx
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ChannelRowActions from '../components/channels/ChannelRowActions';
import { createAppTheme } from '../theme';
import type { AcestreamChannel } from '../services/channelService';

const channel: AcestreamChannel = { id: 'abc', name: 'Alpha', status: 'active', last_seen: '', is_online: true, epg_update_protected: false, tv_channel_id: 7, tv_channel_name: 'Arena TV' };

const mount = (overrides: Partial<AcestreamChannel> = {}) => {
  const handlers = { onPlay: jest.fn(), onCheckStatus: jest.fn(), onEdit: jest.fn(), onToggleHidden: jest.fn(), onAssignTV: jest.fn(), onOpenTV: jest.fn(), onToggleTVFavorite: jest.fn(), onDelete: jest.fn() };
  render(<ThemeProvider theme={createAppTheme('light')}><ChannelRowActions channel={{ ...channel, ...overrides }} {...handlers} /></ThemeProvider>);
  return handlers;
};

it('shows exactly two visible actions: play and check status', () => {
  const handlers = mount();
  const buttons = screen.getAllByRole('button');
  expect(buttons.map((b) => b.getAttribute('aria-label'))).toEqual(['play channel Alpha', 'check channel status Alpha', 'More actions for Alpha']);
  fireEvent.click(screen.getByRole('button', { name: 'play channel Alpha' }));
  expect(handlers.onPlay).toHaveBeenCalledWith(expect.objectContaining({ id: 'abc' }));
});

it('moves the TV link into the menu', () => {
  const handlers = mount();
  fireEvent.click(screen.getByRole('button', { name: 'More actions for Alpha' }));
  fireEvent.click(screen.getByRole('menuitem', { name: 'Open TV channel: Arena TV' }));
  expect(handlers.onOpenTV).toHaveBeenCalled();
});

it('offers linking when the channel has no TV channel', () => {
  const handlers = mount({ tv_channel_id: undefined, tv_channel_name: undefined });
  fireEvent.click(screen.getByRole('button', { name: 'More actions for Alpha' }));
  fireEvent.click(screen.getByRole('menuitem', { name: 'Link to a TV channel' }));
  expect(handlers.onAssignTV).toHaveBeenCalled();
});
```

Update existing tests:
- `ChannelTable.test.tsx`: add `onPlay: jest.fn()` to `handlers()`; where it asserts `go to tv channel …` / `assign tv channel to …` as visible buttons (grep the file), change to: open `More actions for <name>` then assert the `menuitem` (`Open TV channel: …` / `Link to a TV channel`); add an assertion that `play channel <name>` is a visible button.
- `ChannelCardList.test.tsx`: add `onPlay: jest.fn()` to the props; replace `getByRole('button', { name: 'go to tv channel Arena TV' })` with the menu-item assertion (`fireEvent.click(within(card).getByRole('button', { name: 'More actions for Alpha Sports' }))` then `screen.getByRole('menuitem', { name: 'Open TV channel: Arena TV' })`, press Escape); assert `within(card).getByRole('button', { name: 'play channel Alpha Sports' })`.
- `AcestreamChannelsPage.test.tsx`: extend the `ChannelTable` mock with an `onPlay` button (`play ${channel.name}`) and add a test: clicking it renders a dialog titled with the channel name (mock `../components/player/StreamPlayerDialog` with `({ open, title }) => open ? <div role="dialog">{title}</div> : null`).

`e2e/src/pages/channels.ts`: replace `openAssignTv` with the menu route and add helpers:

```ts
  async openAssignTv(name: string): Promise<Locator> {
    await this.rowMenuAction(this.row(name).first(), name, 'Link to a TV channel');
    const dialog = this.dialog('Assign to TV Channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async playChannel(name: string): Promise<void> {
    await this.row(name).first().getByRole('button', { name: `play channel ${name}` }).click();
  }

  /** The TV link lives in the row menu; assert it and close the menu again. */
  async expectLinkedTv(name: string, tvName: string): Promise<void> {
    await this.row(name).first().getByRole('button', { name: `More actions for ${name}` }).click();
    await expect(this.page.getByRole('menuitem', { name: `Open TV channel: ${tvName}` })).toBeVisible();
    await this.page.keyboard.press('Escape');
  }
```

`e2e/tests/07-tv-channels.spec.ts:155` — replace the visible `go to tv channel …` button expectation with `await channels.expectLinkedTv(created.name, spec.name);` (keep the `TV: ${spec.name}` text check).

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npm test -- ChannelRowActions.test.tsx ChannelTable.test.tsx ChannelCardList.test.tsx AcestreamChannelsPage.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement**

`ChannelRowActions.tsx`: add `onPlay: (channel: AcestreamChannel) => void;` to `ChannelActionHandlers`; import `PlayArrowRounded` from `@mui/icons-material/PlayArrowRounded`; render, as the first visible button:

```tsx
      <Tooltip title="Play in the browser">
        <IconButton
          size="small"
          color="primary"
          aria-label={`play channel ${channel.name}`}
          onClick={(event) => {
            event.stopPropagation();
            onPlay(channel);
          }}
        >
          <PlayArrowRounded fontSize="small" />
        </IconButton>
      </Tooltip>
```

keep the Check status button second, delete the visible TV/Link button, and prepend to `menuActions`:

```tsx
    channel.tv_channel_id
      ? { label: `Open TV channel: ${linkedName}`, icon: <TvIcon fontSize="small" />, onClick: () => onOpenTV(channel) }
      : { label: 'Link to a TV channel', icon: <LinkIcon fontSize="small" />, onClick: () => onAssignTV(channel) },
```

Update the component doc comment ("Two visible actions (play, check status) …").

`ChannelTable.tsx`: destructure `onPlay`, pass it to `ChannelRowActions`, add it to the `useMemo` deps.

`AcestreamChannels.tsx`: add `const [playerTarget, setPlayerTarget] = useState<{ contentId: string; title: string } | null>(null);`, `onPlay: (channel) => setPlayerTarget({ contentId: channel.id, title: channel.name })` in `rowHandlers`, and render `<StreamPlayerDialog open={Boolean(playerTarget)} contentId={playerTarget?.contentId ?? null} title={playerTarget?.title ?? ''} onClose={() => setPlayerTarget(null)} />` next to `{confirmDialog}` (import from `../components/player/StreamPlayerDialog`).

- [ ] **Step 4: Run**

Run: `cd frontend && npm test -- ChannelRowActions.test.tsx ChannelTable.test.tsx ChannelCardList.test.tsx AcestreamChannelsPage.test.tsx && npm run lint -- --max-warnings=0 && npm run typecheck && cd ../e2e && npx tsc --noEmit -p . 2>/dev/null || true`
Expected: Jest PASS; lint/typecheck PASS. (The e2e typecheck is best-effort: run it if `e2e/node_modules` exists.)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/channels/ChannelRowActions.tsx frontend/src/components/ChannelTable.tsx frontend/src/pages/AcestreamChannels.tsx frontend/src/__tests__/ChannelRowActions.test.tsx frontend/src/__tests__/ChannelTable.test.tsx frontend/src/__tests__/ChannelCardList.test.tsx frontend/src/__tests__/AcestreamChannelsPage.test.tsx e2e/src/pages/channels.ts e2e/tests/07-tv-channels.spec.ts
git commit -m "feat(frontend): Play action on channel rows; TV link moves into the row menu"
```

---

### Task 7: Play from TV channel detail, TV channels table and Search

**Files:**
- Modify: `frontend/src/pages/TVChannelDetail.tsx`, `frontend/src/components/TVChannelsTable.tsx`, `frontend/src/pages/TVChannels.tsx`, `frontend/src/pages/Search.tsx`
- Tests: `frontend/src/__tests__/TVChannelDetail.test.tsx`, `frontend/src/__tests__/TVChannelsTable.test.tsx`, `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx`, `frontend/src/__tests__/Search.test.tsx`

**Interfaces:**
- Produces: `TVChannelsTableProps.onPlay?: (channel: TVChannel) => void` (button disabled when the channel has no streams); detail page buttons `play stream ${name}` per stream and `Play best stream` in the header; Search button `play ${name}` per result.

- [ ] **Step 1: Write the failing tests**

In each test file mock the dialog once: `jest.mock('../components/player/StreamPlayerDialog', () => ({ __esModule: true, default: ({ open, title, contentId }: { open: boolean; title: string; contentId: string | null }) => (open ? <div role="dialog" aria-label={title}>{contentId}</div> : null) }));`

`TVChannelDetail.test.tsx` — add:

```tsx
  it('plays a single stream and the best stream from the header', () => {
    mockUseTVChannel.mockReturnValue({ data: { ...baseChannel, acestream_channels: [
      { id: 'ace-best', name: 'Arena Feed 1', group: 'Sports', is_online: true },
      { id: 'ace-2', name: 'Arena Feed 2', group: 'Sports', is_online: false },
    ] }, isLoading: false, isError: false });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'play stream Arena Feed 2' }));
    expect(screen.getByRole('dialog', { name: 'Arena Feed 2' })).toHaveTextContent('ace-2');
    fireEvent.click(screen.getByRole('button', { name: 'Play best stream' }));
    expect(screen.getByRole('dialog', { name: 'Arena TV' })).toHaveTextContent('ace-best');
  });
```

`TVChannelsTable.test.tsx` — add (both desktop and compact):

```tsx
  it('offers Play next to Open and disables it without streams', () => {
    const onPlay = jest.fn();
    renderTable(<TVChannelsTable {...baseProps} channels={[{ ...channelWithStreams, name: 'With streams' }, { ...channelWithStreams, id: 2, name: 'Empty', acestream_channels: [] }]} onPlay={onPlay} />);
    fireEvent.click(screen.getByRole('button', { name: 'play tv channel With streams' }));
    expect(onPlay).toHaveBeenCalledWith(expect.objectContaining({ name: 'With streams' }));
    expect(screen.getByRole('button', { name: 'play tv channel Empty' })).toBeDisabled();
  });
```
(`channelWithStreams` = the file's existing channel fixture with `acestream_channels: [{ id: 'ace-1', name: 'Feed', is_active: true, is_online: true, epg_update_protected: false, channel_id: 'ace-1' }]`; adapt to the fixture name used in that file.)

`TVChannelsPageResponsive.test.tsx` — the `TVChannelsTable` mock gains an `onPlay` prop and a test asserts that calling it with a channel opens the dialog with `acestream_channels[0].id`.

`Search.test.tsx` — add:

```tsx
  it('plays a result without adding it', () => {
    configureSearchMock();
    renderPage();  // use the file's existing render + search helpers
    runSearch('arena');
    fireEvent.click(screen.getByRole('button', { name: 'play Arena Premium' }));
    expect(screen.getByRole('dialog', { name: 'Arena Premium' })).toHaveTextContent('ace-1');
  });
```
(adapt `renderPage`/`runSearch` to the helpers already in the file).

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npm test -- TVChannelDetail.test.tsx TVChannelsTable.test.tsx TVChannelsPageResponsive.test.tsx Search.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement**

`TVChannelDetail.tsx`: state `const [playerTarget, setPlayerTarget] = useState<{ contentId: string; title: string } | null>(null);`; header actions: add before Edit `<Button variant="contained" size="small" startIcon={<PlayArrowRounded />} disabled={streamCount === 0} onClick={() => setPlayerTarget({ contentId: channel.acestream_channels[0].id, title: channel.name })}>Play best stream</Button>` (the API returns streams best-first); in the Streams list `secondaryAction` group add before Remove `<Tooltip title="Play in the browser"><IconButton edge="end" color="primary" aria-label={`play stream ${acestream.name}`} onClick={() => setPlayerTarget({ contentId: acestream.id, title: acestream.name })}><PlayArrowRounded /></IconButton></Tooltip>` and widen the ListItem `pr` to 12; render `<StreamPlayerDialog … />`.

`TVChannelsTable.tsx`: add `onPlay?: (channel: TVChannel) => void` prop; in `renderActions` add a Play control before Open in both layouts: desktop `IconButton` (`aria-label={`play tv channel ${channel.name}`}`, `disabled={!onPlay || !(channel.acestream_channels?.length)}`), mobile `Button` with the same label; widen the actions column to 240.

`TVChannels.tsx`: state + `onPlay={(channel) => setPlayerTarget({ contentId: channel.acestream_channels[0].id, title: channel.name })}` + dialog.

`Search.tsx`: in the Action cell add `<Button size="small" startIcon={<PlayArrowRounded />} onClick={() => setPlayerTarget({ contentId: channel.id, title: channel.name })} aria-label={`play ${channel.name}`}>Play</Button>` before the Add button/chip (wrap both in a `Stack direction="row" spacing={1}`); state + dialog.

- [ ] **Step 4: Run**

Run: `cd frontend && npm test -- TVChannelDetail.test.tsx TVChannelsTable.test.tsx TVChannelsPageResponsive.test.tsx Search.test.tsx && npm run lint -- --max-warnings=0 && npm run typecheck`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/TVChannelDetail.tsx frontend/src/components/TVChannelsTable.tsx frontend/src/pages/TVChannels.tsx frontend/src/pages/Search.tsx frontend/src/__tests__/TVChannelDetail.test.tsx frontend/src/__tests__/TVChannelsTable.test.tsx frontend/src/__tests__/TVChannelsPageResponsive.test.tsx frontend/src/__tests__/Search.test.tsx
git commit -m "feat(frontend): Play from TV channel detail, TV channels list and search results"
```

---

### Task 8: Docs and command-builder facts for the player

**Files:**
- Create: `wiki/Web-Player.md`
- Modify: `docs/builder/runtime-options.json` (`player` block + `notes.publicBaseUrl`), `docs/builder/app.js` + `docs/index.html` (Advanced inputs for `PUBLIC_BASE_URL`, `TUNER_ALLOWED_NETWORKS`, `PLAYER_MAX_SESSIONS`), `scripts/ci/validate_command_builder.sh` (tuple + default cross-checks), `README.md` (feature paragraph + toggles), `CLAUDE.md`

- [ ] **Step 1: Write the failing validator expectations**

Append to `backend/tests/test_runtime_integration_guards.py`:

```python
def test_command_builder_declares_player_facts_and_emits_the_new_env():
    import json
    data = json.loads((REPO_ROOT / "docs" / "builder" / "runtime-options.json").read_text())
    app_js = (REPO_ROOT / "docs" / "builder" / "app.js").read_text()
    validator = (REPO_ROOT / "scripts" / "ci" / "validate_command_builder.sh").read_text()

    assert data["player"]["maxSessionsDefault"] == 3
    assert data["player"]["hlsDirDefault"] == "/tmp/acestream-player"
    assert data["player"]["tunerNetworksDefault"].startswith("127.0.0.0/8,10.0.0.0/8,100.64.0.0/10")
    assert "publicBaseUrl" in data["notes"]
    for name in ("PUBLIC_BASE_URL", "TUNER_ALLOWED_NETWORKS", "PLAYER_MAX_SESSIONS"):
        assert f"'{name}'" in app_js, name
        assert f'"{name}"' in validator, name
```

- [ ] **Step 2: Implement**

`docs/builder/runtime-options.json` — add a top-level block:

```json
  "player": {
    "hlsDirDefault": "/tmp/acestream-player",
    "hlsDirShmHint": "Set PLAYER_HLS_DIR=/dev/shm/acestream-player with a larger --shm-size to keep player segments in RAM.",
    "maxSessionsDefault": 3,
    "tunerNetworksDefault": "127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10",
    "description": "The web player and the Jellyfin/Plex tuner routes ship in every flavor; ffmpeg is bundled."
  }
```

and to `notes`: `"publicBaseUrl": "Jellyfin, Plex and VLC need an address they can reach: set it under Integrations → Public address, or pass PUBLIC_BASE_URL."`.

`docs/index.html` — inside the existing Advanced `<details>` add three labelled inputs with ids `public-base-url-input` (placeholder `http://192.168.1.10:8000`), `tuner-networks-input` (placeholder = `tunerNetworksDefault`) and `player-max-sessions-input` (type number, min 1). `docs/builder/app.js` — `state` keys `publicBaseUrl: ''`, `tunerNetworks: ''`, `playerMaxSessions: ''`; `bind()` them; in `envEntries()`:

```js
  if (state.publicBaseUrl.trim()) env.push(['PUBLIC_BASE_URL', state.publicBaseUrl.trim()]);
  if (state.tunerNetworks.trim()) env.push(['TUNER_ALLOWED_NETWORKS', state.tunerNetworks.trim()]);
  if (/^\d+$/.test(state.playerMaxSessions.trim())) env.push(['PLAYER_MAX_SESSIONS', state.playerMaxSessions.trim()]);
```

and render `notes.publicBaseUrl` in the `afterRun` block; change the web port emission to `-p 0.0.0.0:8000:8000` (run: `-p 0.0.0.0:${port}:8000`; compose: `"0.0.0.0:${port}:8000"`).

`scripts/ci/validate_command_builder.sh` — extend the tuple with `"PUBLIC_BASE_URL", "TUNER_ALLOWED_NETWORKS", "PLAYER_MAX_SESSIONS"` and add:

```python
if data["player"]["maxSessionsDefault"] != int(re.search(r'PLAYER_MAX_SESSIONS:-(\d+)', entrypoint).group(1)):
    errors.append("player.maxSessionsDefault differs from PLAYER_MAX_SESSIONS default in entrypoint.sh")
if data["player"]["tunerNetworksDefault"] != re.search(r'TUNER_ALLOWED_NETWORKS:-([^}]+)\}', entrypoint).group(1):
    errors.append("player.tunerNetworksDefault differs from TUNER_ALLOWED_NETWORKS default in entrypoint.sh")
```

`wiki/Web-Player.md`: what it does (one ffmpeg per channel, audio re-encoded to AAC, ~6-10 s behind live), requirements (bundled ffmpeg; `FFMPEG_BINARY_PATH` to use your own; ARM in-container engine caveat), the Play buttons, the status/error messages and what to do (VLC/Kodi via the stream link), the knobs (`PLAYER_MAX_SESSIONS`, `PLAYER_HLS_DIR`, `PLAYER_START_TIMEOUT_SECONDS`), and the API token behaviour (copied stream links carry `?token=`).

`README.md`: a "Web player" paragraph in the feature list and the three env rows in "Docker Runtime Toggles". `CLAUDE.md`: add the player domain (service, endpoints, lifespan start/stop, fake ffmpeg in tests) and the ffmpeg-builder stage to the Docker section.

- [ ] **Step 3: Run**

Run: `bash scripts/ci/validate_command_builder.sh && PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_runtime_integration_guards.py`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add wiki/Web-Player.md docs/builder/runtime-options.json docs/builder/app.js docs/index.html scripts/ci/validate_command_builder.sh README.md CLAUDE.md backend/tests/test_runtime_integration_guards.py
git commit -m "docs(player): web player guide, command-builder inputs and validator checks"
```

---

### Task 9: Contracts, codegen and full verification


**Carry-forward fixes from the Plan 1 whole-branch review** (do these first, each with a test where behavioural):
- `CLAUDE.md` dev-server command: add `--no-proxy-headers` so it matches the runtime contract in spec 4.3.
- `backend/main.py` relay-reaper loop: wrap the loop body in `try/except Exception: logger.exception(...)` so one failure does not end reaping, and add a lifespan test that a raising `reap_finished` does not kill the task.
- `backend/app/api/endpoints/tuner.py` 422 path: raise `APIError` so the body uses the `{"error": {...}}` envelope like the 403/502 on the same router; assert the envelope in the tuner tests.
- `backend/app/services/engine_client.py`: `startswith(("http://", "https://"))` instead of `startswith("http")`, and merge the stop parameter with `httpx.URL(...).copy_merge_params({"method": "stop"})` so an existing query on `command_url` survives; two tests.
- `backend/Dockerfile` `CMD`: add `--no-proxy-headers --timeout-graceful-shutdown 3` (or drop the CMD in favour of the entrypoint) and extend `backend/tests/test_runtime_integration_guards.py` to cover this fourth launch path.

- [ ] **Step 1: Regenerate and run everything**

```bash
backend/venv/bin/python backend/scripts/dump_openapi.py
cd frontend && npm run codegen && cd ..
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests --ignore=backend/tests/docker
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_vendor.py
cd frontend && npm run lint -- --max-warnings=0 && npm run typecheck && CI=true npm test -- --watch=false && npm run build && cd ..
bash scripts/ci/run_v2_test_suite.sh --profile quick
python3 scripts/ci/validate_docker_manifest_metadata.py && bash scripts/ci/validate_command_builder.sh
```
Expected: all PASS.

- [ ] **Step 2: Contract test**

Add to `backend/tests/contracts/test_integrations_contracts.py` (create; register it in the quick profile list in `scripts/ci/run_v2_test_suite.sh` next to the other contracts files): request-DTO validation for `PlayerSessionCreate` (40 hex) and exact response key sets for `GET /api/v1/player/capabilities` (`{"ffmpeg_available","ffmpeg_path","max_sessions","hls_dir"}`) and `GET /api/v1/player/sessions` (`{"sessions"}`), plus `GET /api/v1/system/public-url` (`{"url","source","warnings"}`).

- [ ] **Step 3: Commit**

```bash
git add backend/openapi.json frontend/src/types/api-generated.ts backend/tests/contracts/test_integrations_contracts.py scripts/ci/run_v2_test_suite.sh
git commit -m "chore(contracts): player and public-url DTOs in OpenAPI, types and the quick profile"
```

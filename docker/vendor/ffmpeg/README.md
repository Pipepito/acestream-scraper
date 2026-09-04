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

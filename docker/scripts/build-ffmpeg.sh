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
    STRIP="strip"
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
version="${VENDORED_FILE#ffmpeg-}"
printf 'ffmpeg_version=%s\ntargetarch=%s\ntargetvariant=%s\nsha256=%s\n' \
    "${version%.tar.*}" "$TARGETARCH" "$TARGETVARIANT" "$SHA256" > "$OUT_DIR/install-metadata.txt"
log "built static ffmpeg for $TARGETARCH${TARGETVARIANT:+/$TARGETVARIANT}: $(stat -c %s "$OUT_DIR/ffmpeg") bytes"

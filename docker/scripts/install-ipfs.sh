#!/usr/bin/env bash
# Installs the Kubo (go-ipfs) daemon into /opt/ipfs for the container platform
# being built. Runs inside the Dockerfile's `ipfs-installer` stage.
#
# Kubo ships as a static Go binary, so the stage runs on $BUILDPLATFORM and
# simply downloads the tarball for $TARGETPLATFORM — no QEMU emulation needed.
# Downloads come from the GitHub release (https://github.com/ipfs/kubo/releases)
# and are verified against the sha512 digests pinned below.
#
# Platform support follows upstream: Kubo publishes linux-amd64 and linux-arm64
# builds only — there is no 32-bit ARM build, so on linux/arm/v7 this script
# leaves /opt/ipfs/bin empty and the image ships without IPFS (the entrypoint
# fails cleanly if ENABLE_IPFS=true is requested there). Same pattern as the
# amd64-only cloudflare-warp client.
#
# Output: /opt/ipfs/bin/ipfs (except arm/v7) and
# /opt/ipfs/install-metadata.txt for diagnostics.

set -euo pipefail

KUBO_VERSION="${KUBO_VERSION:-v0.43.0}"
KUBO_BASE_URL="${KUBO_BASE_URL:-https://github.com/ipfs/kubo/releases/download}"
TARGET_PLATFORM="${TARGETPLATFORM:-}"
# IPFS_INSTALL_DIR is overridable so the contract tests can run the script
# directly without touching /opt.
IPFS_DIR="${IPFS_INSTALL_DIR:-/opt/ipfs}"
IPFS_BIN_DIR="$IPFS_DIR/bin"
SRC_DIR="${IPFS_INSTALL_SRC_DIR:-/tmp/ipfs-src}"

log() { printf 'install-ipfs: %s\n' "$*"; }
fail() { printf 'install-ipfs: %s\n' "$*" >&2; exit 1; }

mkdir -p "$IPFS_DIR" "$IPFS_BIN_DIR" "$SRC_DIR"

[ -n "$TARGET_PLATFORM" ] || fail "TARGETPLATFORM is not set (pass --platform to docker buildx build)"

# Per-release, per-arch sha512 pins (from the *.tar.gz.sha512 release assets).
# Bumping KUBO_VERSION requires refreshing these digests.
case "$TARGET_PLATFORM" in
    linux/amd64)
        KUBO_ASSET="linux-amd64"
        KUBO_SHA512="6af21cd24a307d94326807b3d3827064c74fb7122f83b6940af250e6ae40da250e0ec0e1f3551256b78cd204623ed56c32ce735bbe28bdcc787b36943c52458a"
        ;;
    linux/arm64|linux/arm64/v8)
        KUBO_ASSET="linux-arm64"
        KUBO_SHA512="aae6c766ec2436f27bbd2d6ab5f8de7d2ced4dc83abc5b54b17bd58a80c28f1ea2e38840305e22f08bd01c55cf8263745675da1bbda2ac0bcde268e9e61e3818"
        ;;
    linux/arm/v7|linux/arm/v6)
        log "Kubo publishes no 32-bit ARM build; installing nothing for $TARGET_PLATFORM"
        printf 'kubo_version=none\nplatform=%s\nreason=no upstream 32-bit ARM build\n' \
            "$TARGET_PLATFORM" > "$IPFS_DIR/install-metadata.txt"
        exit 0
        ;;
    *)
        fail "unsupported TARGETPLATFORM for Kubo: $TARGET_PLATFORM"
        ;;
esac

TARBALL="kubo_${KUBO_VERSION}_${KUBO_ASSET}.tar.gz"
URL="$KUBO_BASE_URL/$KUBO_VERSION/$TARBALL"

log "downloading $URL"
curl -fsSL --retry 3 --retry-delay 2 -o "$SRC_DIR/$TARBALL" "$URL"

log "verifying sha512"
printf '%s  %s\n' "$KUBO_SHA512" "$SRC_DIR/$TARBALL" | sha512sum -c - >/dev/null \
    || fail "sha512 mismatch for $TARBALL"

tar -xzf "$SRC_DIR/$TARBALL" -C "$SRC_DIR"
[ -f "$SRC_DIR/kubo/ipfs" ] || fail "tarball did not contain kubo/ipfs"
install -m 0755 "$SRC_DIR/kubo/ipfs" "$IPFS_BIN_DIR/ipfs"

printf 'kubo_version=%s\nplatform=%s\nasset=%s\nsha512=%s\n' \
    "$KUBO_VERSION" "$TARGET_PLATFORM" "$KUBO_ASSET" "$KUBO_SHA512" \
    > "$IPFS_DIR/install-metadata.txt"

rm -rf "$SRC_DIR"
log "installed Kubo $KUBO_VERSION for $TARGET_PLATFORM"

#!/usr/bin/env bash
# Build the pinned Kubo release with security-patched module locks and Go.
# Runs on BUILDPLATFORM; only the resulting static binary is shipped.
set -euo pipefail

KUBO_VERSION="${KUBO_VERSION:-v0.43.1}"
KUBO_COMMIT=acc53c093810a8fe9a4bc2f023f0b1e0c1d629b5
KUBO_SOURCE_SHA256=b744b98b00bcb775a19001b468e460a4f228d16033a3789382e5b07e09b76ae6
TARGET_PLATFORM="${TARGETPLATFORM:-}"
IPFS_DIR="${IPFS_INSTALL_DIR:-/opt/ipfs}"
SRC_DIR="${IPFS_INSTALL_SRC_DIR:-/tmp/ipfs-src}"
LOCK_DIR="${IPFS_LOCK_DIR:-/usr/local/lib/ipfs-install}"

log() { printf 'install-ipfs: %s\n' "$*"; }
fail() { printf 'install-ipfs: %s\n' "$*" >&2; exit 1; }

mkdir -p "$IPFS_DIR/bin" "$SRC_DIR"
[ -n "$TARGET_PLATFORM" ] || fail "TARGETPLATFORM is not set (pass --platform to docker buildx build)"
case "$TARGET_PLATFORM" in
    linux/amd64) GOARCH=amd64 ;;
    linux/arm64|linux/arm64/v8) GOARCH=arm64 ;;
    linux/arm/v7|linux/arm/v6)
        log "Kubo publishes no 32-bit ARM build; installing nothing for $TARGET_PLATFORM"
        printf 'kubo_version=none\nplatform=%s\nreason=no upstream 32-bit ARM build\n' \
            "$TARGET_PLATFORM" > "$IPFS_DIR/install-metadata.txt"
        exit 0 ;;
    *) fail "unsupported TARGETPLATFORM for Kubo: $TARGET_PLATFORM" ;;
esac
[ "$KUBO_VERSION" = v0.43.1 ] || fail "KUBO_VERSION does not match the reviewed source and module locks"
[ "$(go env GOVERSION)" = go1.27.3 ] || fail "Kubo requires the reviewed Go 1.27.3 toolchain"

URL="https://codeload.github.com/ipfs/kubo/tar.gz/$KUBO_COMMIT"
log "downloading pinned Kubo source"
curl -fsSL --retry 3 --retry-delay 2 -o "$SRC_DIR/source.tar.gz" "$URL"
printf '%s  %s\n' "$KUBO_SOURCE_SHA256" "$SRC_DIR/source.tar.gz" | sha256sum -c - \
    || fail "sha256 mismatch for Kubo source"
tar -xzf "$SRC_DIR/source.tar.gz" -C "$SRC_DIR" --strip-components=1
cp "$LOCK_DIR/go.mod" "$LOCK_DIR/go.sum" "$SRC_DIR/"
cd "$SRC_DIR"
export GOTOOLCHAIN=local
# No resolver updates during image builds. Checksums remain in the public tree.
go mod download
go mod verify
log "cross-compiling Kubo for $TARGET_PLATFORM"
CGO_ENABLED=0 GOOS=linux GOARCH="$GOARCH" go build -mod=readonly -trimpath -buildvcs=false \
    -ldflags "-s -w -X github.com/ipfs/kubo.CurrentCommit=$KUBO_COMMIT-security -X github.com/ipfs/kubo.buildOrigin=github.com/Pipepito/acestream-scraper" \
    -o "$IPFS_DIR/bin/ipfs" ./cmd/ipfs
printf 'kubo_version=%s\nplatform=%s\nsource_commit=%s\nsource_sha256=%s\ngo=%s\n' \
    "$KUBO_VERSION" "$TARGET_PLATFORM" "$KUBO_COMMIT" "$KUBO_SOURCE_SHA256" "$(go env GOVERSION)" \
    > "$IPFS_DIR/install-metadata.txt"
cd /
rm -rf "$SRC_DIR"
log "installed Kubo $KUBO_VERSION security rebuild for $TARGET_PLATFORM"

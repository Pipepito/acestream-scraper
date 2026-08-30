#!/usr/bin/env bash
# Installs a self-contained ZeroNet node (zeronet-conservancy) into
# /opt/zeronet for the container platform being built. Runs inside the
# Dockerfile's `zeronet-installer` stage.
#
# ZeroNet is bundled for linux/amd64 only, like the v1 image (and like the
# amd64-only cloudflare-warp client): its dependency set needs gevent 23.9.x
# (see docker/zeronet/requirements.txt), which has no wheels for modern ARM
# targets worth supporting, and the node has never been validated there. On
# other platforms this script leaves /opt/zeronet empty except for metadata
# and the entrypoint refuses ENABLE_ZERONET=true with a clear error — an
# external ZeroNet service through ZERONET_URL keeps working everywhere.
#
# The stage runs on $BUILDPLATFORM (so ARM image builds skip it natively,
# without QEMU); the pip wheels it installs are for the interpreter it runs
# on, so an amd64 payload can only be produced on an amd64 build host — the
# script fails loudly on a cross-build rather than embedding wrong-arch
# wheels.
#
# The source is pinned by git commit (tag v0.7.10): the clone is checked
# against ZERONET_COMMIT after checkout, which gives content integrity
# without relying on byte-stable GitHub archive tarballs.
#
# Output: /opt/zeronet/app (source), /opt/zeronet/python (the stage's whole
# CPython prefix, site-packages included), /opt/zeronet/bin/zeronet
# (launcher), /opt/zeronet/install-metadata.txt for diagnostics.

set -euo pipefail

ZERONET_REPO_URL="${ZERONET_REPO_URL:-https://github.com/zeronet-conservancy/zeronet-conservancy}"
ZERONET_REF="${ZERONET_REF:-v0.7.10}"
ZERONET_COMMIT="${ZERONET_COMMIT:-18d35d3bed4f0683e99f8af5a86a8d76ed866e1e}"
TARGET_PLATFORM="${TARGETPLATFORM:-}"
# Overridable so the contract tests can run the script directly without
# touching /opt.
ZN_DIR="${ZERONET_INSTALL_DIR:-/opt/zeronet}"
REQUIREMENTS="${ZERONET_REQUIREMENTS:-/tmp/zeronet-requirements.txt}"

log() { printf 'install-zeronet: %s\n' "$*"; }
fail() { printf 'install-zeronet: %s\n' "$*" >&2; exit 1; }

mkdir -p "$ZN_DIR"

[ -n "$TARGET_PLATFORM" ] || fail "TARGETPLATFORM is not set (pass --platform to docker buildx build)"

case "$TARGET_PLATFORM" in
    linux/amd64)
        ;;
    linux/arm64|linux/arm64/v8|linux/arm/v7|linux/arm/v6)
        log "ZeroNet is bundled for linux/amd64 only; installing nothing for $TARGET_PLATFORM"
        printf 'zeronet_version=none\nplatform=%s\nreason=bundled for linux/amd64 only\n' \
            "$TARGET_PLATFORM" > "$ZN_DIR/install-metadata.txt"
        exit 0
        ;;
    *)
        fail "unsupported TARGETPLATFORM for ZeroNet: $TARGET_PLATFORM"
        ;;
esac

if [ "$(uname -m)" != "x86_64" ]; then
    fail "the amd64 ZeroNet payload can only be built on an amd64 build host (got $(uname -m)); pip would embed wrong-arch wheels"
fi

[ -f "$REQUIREMENTS" ] || fail "requirements file not found: $REQUIREMENTS"

PYTHON_BIN="${ZERONET_PYTHON_BIN:-python3}"
PYTHON_PREFIX="$("$PYTHON_BIN" -c 'import sys; print(sys.prefix)')"

log "cloning $ZERONET_REPO_URL @ $ZERONET_REF"
git clone --depth 1 --branch "$ZERONET_REF" "$ZERONET_REPO_URL" "$ZN_DIR/app"
actual_commit="$(git -C "$ZN_DIR/app" rev-parse HEAD)"
if [ "$actual_commit" != "$ZERONET_COMMIT" ]; then
    fail "ref $ZERONET_REF resolved to $actual_commit, expected pinned commit $ZERONET_COMMIT"
fi
rm -rf "$ZN_DIR/app/.git"

log "installing python dependencies"
"$PYTHON_BIN" -m pip install --no-cache-dir -r "$REQUIREMENTS"

# Carry the whole interpreter prefix along: the runtime image runs the app on
# a different CPython, so ZeroNet brings its own (binary, stdlib, libpython
# and the site-packages just installed) under /opt/zeronet/python. CPython
# locates its prefix relative to the executable, so the tree is relocatable;
# the launcher only needs LD_LIBRARY_PATH for libpython.
log "staging interpreter prefix from $PYTHON_PREFIX"
mkdir -p "$ZN_DIR/python"
cp -a "$PYTHON_PREFIX/bin" "$PYTHON_PREFIX/lib" "$ZN_DIR/python/"

PY_TAG="$(basename "$(ls -d "$ZN_DIR"/python/lib/python3.* | head -n 1)")"
[ -x "$ZN_DIR/python/bin/$PY_TAG" ] || fail "staged interpreter $PY_TAG is missing its binary"

mkdir -p "$ZN_DIR/bin"
cat > "$ZN_DIR/bin/zeronet" <<LAUNCHER
#!/bin/bash
set -e
export LD_LIBRARY_PATH="$ZN_DIR/python/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
cd "$ZN_DIR/app"
exec "$ZN_DIR/python/bin/$PY_TAG" zeronet.py "\$@"
LAUNCHER
chmod +x "$ZN_DIR/bin/zeronet"

printf 'zeronet_version=%s\ncommit=%s\nplatform=%s\npython=%s\n' \
    "$ZERONET_REF" "$ZERONET_COMMIT" "$TARGET_PLATFORM" "$PY_TAG" \
    > "$ZN_DIR/install-metadata.txt"

log "installed zeronet-conservancy $ZERONET_REF ($ZERONET_COMMIT) with $PY_TAG"

#!/usr/bin/env bash
# Installs a self-contained ZeroNet node (zeronet-conservancy) into
# /opt/zeronet for the container platform being built. Runs inside the
# Dockerfile's `zeronet-installer` stage.
#
# ZeroNet is bundled for linux/amd64 and linux/arm64. 32-bit ARM is still
# excluded: gevent publishes no armv7l wheels (checked on PyPI for both the
# old 23.9.1 and the current pin), so linux/arm/v7 and linux/arm/v6 would have
# to build gevent, greenlet and coincurve from source inside the image. On
# those platforms this script leaves /opt/zeronet empty except for metadata
# and the entrypoint refuses ENABLE_ZERONET=true with a clear error — an
# external ZeroNet service through ZERONET_URL keeps working everywhere.
#
# WHY arm64 IS IN NOW. It used to be excluded with the same reasoning as
# armv7 ("gevent 23.9.x has no wheels for modern ARM targets"), but that was
# only ever true for 32-bit: gevent has published manylinux aarch64 wheels
# throughout. What actually blocked arm64 was the *ZeroNet* pin, v0.7.10,
# which deadlocks under gevent >= 24.10 and therefore forced gevent 23.9.1 —
# and 23.9.1 has no aarch64 wheel for the interpreters this image uses. With
# the node moved past that (see below), the constraint disappears.
#
# The stage runs on $TARGETPLATFORM, not $BUILDPLATFORM: the pip wheels and
# the staged CPython prefix are native code, so they have to be produced for
# the platform they will run on. Cross-building them is what the old
# `uname -m` guard was defending against; running under emulation removes the
# hazard instead of detecting it.
#
# The source is pinned by COMMIT and fetched by commit, not by tag or branch:
# `git fetch --depth 1 origin <sha>` is served by GitHub, so the pin cannot
# drift when a branch moves and there is no need for a tag to exist.
#
# /opt/zeronet/app/.git IS KEPT ON PURPOSE. The node reads its own build
# information through GitPython (src/util/Git.py); with the directory removed
# it dies at import time with
#     ImportError: cannot import name 'Build' from 'src'
# A --depth 1 checkout costs a few MB and is the cheapest way to satisfy it.
#
# Output: /opt/zeronet/app (source), /opt/zeronet/python (the stage's whole
# CPython prefix, site-packages included), /opt/zeronet/bin/zeronet
# (launcher), /opt/zeronet/install-metadata.txt for diagnostics.

set -euo pipefail

ZERONET_REPO_URL="${ZERONET_REPO_URL:-https://github.com/zeronet-conservancy/zeronet-conservancy}"
ZERONET_REF="${ZERONET_REF:-main}"
ZERONET_COMMIT="${ZERONET_COMMIT:-81d3ffc6bdfb600e9a1d4a091f1ceb131d92c4f1}"
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
        expected_machine=x86_64
        ;;
    linux/arm64|linux/arm64/v8)
        expected_machine=aarch64
        ;;
    linux/arm/v7|linux/arm/v6)
        log "ZeroNet is not bundled for $TARGET_PLATFORM (no armv7l wheels for gevent); installing nothing"
        printf 'zeronet_version=none\nplatform=%s\nreason=no armv7l wheels for gevent\n' \
            "$TARGET_PLATFORM" > "$ZN_DIR/install-metadata.txt"
        exit 0
        ;;
    *)
        fail "unsupported TARGETPLATFORM for ZeroNet: $TARGET_PLATFORM"
        ;;
esac

# The stage must run AS the target platform (buildx does this with binfmt).
# Building the payload anywhere else would embed wrong-arch wheels and a
# wrong-arch interpreter, and the failure would only show at runtime.
if [ "$(uname -m)" != "$expected_machine" ]; then
    fail "the $TARGET_PLATFORM ZeroNet payload must be built on $expected_machine (got $(uname -m)); the zeronet-installer stage needs --platform=\$TARGETPLATFORM"
fi

[ -f "$REQUIREMENTS" ] || fail "requirements file not found: $REQUIREMENTS"

PYTHON_BIN="${ZERONET_PYTHON_BIN:-python3}"
PYTHON_PREFIX="$("$PYTHON_BIN" -c 'import sys; print(sys.prefix)')"

log "fetching $ZERONET_REPO_URL @ $ZERONET_COMMIT ($ZERONET_REF)"
mkdir -p "$ZN_DIR/app"
git -C "$ZN_DIR/app" init -q .
git -C "$ZN_DIR/app" remote add origin "$ZERONET_REPO_URL"
git -C "$ZN_DIR/app" fetch -q --depth 1 origin "$ZERONET_COMMIT"
git -C "$ZN_DIR/app" checkout -q FETCH_HEAD
actual_commit="$(git -C "$ZN_DIR/app" rev-parse HEAD)"
if [ "$actual_commit" != "$ZERONET_COMMIT" ]; then
    fail "fetched $actual_commit, expected pinned commit $ZERONET_COMMIT"
fi
# NO `rm -rf .git` here: src/util/Git.py reads the repository through
# GitPython at import time and the node will not start without it.

# zeronet-conservancy 81d3ffc6 discards every content.json a peer serves it.
# ContentManager.verifyContent() compares a Path against the str it was given:
#
#     if content.get('inner_path') and Path(content['inner_path']) != inner_path:
#         raise VerifyError(f"Wrong inner_path: {content['inner_path']}")
#
# inner_path arrives as a string -- Worker.py passes task["inner_path"], and
# the same function compares it against the literal "content.json" a few lines
# above -- and in Python a Path is never equal to a str, so the condition is
# True for every site whose content.json declares its own inner_path. That is
# all of them.
#
# Measured with two nodes on the same network at the same time, one patched:
#
#     "Wrong inner_path" rejections     970 -> 0
#     peers that delivered a file         0 -> 3
#
# End to end, the patched node downloaded a complete zite from the network for
# the first time. Without the patch the node connects, does PEX, announces on
# DHT and throws away everything it is handed, which is indistinguishable from
# an empty network.
#
# Patched here rather than by moving the pin because 81d3ffc6 IS the tip of
# zeronet-conservancy's main branch: there is nothing newer to pin to.
#
# Three more comparisons in the same file have the same Path/str mismatch and
# are NOT touched here, because only this one was measured:
#
#     918  inner_path == Path('content.json')   always False -> the root
#          content.json size limit never fires
#     933  inner_path == Path('content.json')   always False -> harmless in
#          practice: getRules() normalises its argument, so the root takes the
#          include branch and still passes
#     781/800 the same, inside sign()
#
# If anyone revisits them: do NOT fix this by normalising inner_path to Path
# at the top of verifyContent (the shape getRules already uses). Line 900 in
# that same function compares inner_path against the *string* "content.json"
# and works today; normalising breaks it, and breaks line 722 in sign() too.
# Correct the comparisons one by one and leave the variable a str.
#
# The patch fails loudly when the line is not found, so bumping the pin stops
# the build instead of silently applying nothing.
log "patching ContentManager inner_path comparison"
"$PYTHON_BIN" - "$ZN_DIR/app/src/Content/ContentManager.py" <<'INNER_PATH_PATCH'
import sys

OLD = ("if content.get('inner_path') and "
       "Path(content['inner_path']) != inner_path:")
NEW = ("if content.get('inner_path') and "
       "Path(content['inner_path']) != Path(inner_path):")

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    src = fh.read()
if NEW in src:
    sys.exit(0)
if src.count(OLD) != 1:
    sys.exit("inner_path patch: expected 1 occurrence in %s, found %d; the "
             "pinned zeronet-conservancy commit has changed and the fix needs "
             "rechecking" % (path, src.count(OLD)))
with open(path, "w", encoding="utf-8") as fh:
    fh.write(src.replace(OLD, NEW, 1))
INNER_PATH_PATCH

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

#!/usr/bin/env bash
# Installs the AceStream engine into /opt/acestream for the container platform
# being built. Runs inside the Dockerfile's `acestream-installer` stage.
#
# Source selection (ACESTREAM_SOURCE):
#   auto      (default) resolve the entry for $TARGETPLATFORM from the manifest
#             at $ACESTREAM_MANIFEST; non-empty ACESTREAM_* env/build-args
#             override the manifest values.
#   explicit  skip the manifest; ACESTREAM_DOWNLOAD_URL and/or
#             ACESTREAM_VENDORED_FILE must be set.
#   fixture   install docker/testdata/acestream (contract tests only).
#
# Every archive (engine payload and, for android-apk, the bionic runtime) is
# resolved in this order and sha256-verified whichever source wins:
#   1. vendored copy   $ACESTREAM_VENDOR_ROOT/<subdir>/<vendored_file>
#   2. upstream URL    ACESTREAM_DOWNLOAD_URL / ACESTREAM_BIONIC_URL
#   3. mirrors         ACESTREAM_MIRROR_URLS / ACESTREAM_BIONIC_MIRROR_URLS
#
# Install kinds:
#   executable   upstream Linux tarball (x86_64 3.2.x): extract, symlink the
#                entry binary, pip-install its requirements.txt.
#   android-apk  official Android engine APK (arm64-v8a / armeabi-v7a): unzip
#                the engine payload, add the Linux bootstrap + launcher, and
#                stage a minimal Android 9 bionic userland under
#                /opt/acestream-system (copied to /system by the runtime stage).
#
# Output: /opt/acestream populated, /opt/acestream/bin/acestreamengine ->
# launcher, /opt/acestream-system (empty unless android-apk),
# /opt/acestream/install-metadata.txt for diagnostics.

set -euo pipefail

ACE_DIR="/opt/acestream"
ACE_BIN_DIR="$ACE_DIR/bin"
SYS_DIR="/opt/acestream-system"
SRC_DIR="/tmp/acestream-src"
FIXTURE_DIR="${ACESTREAM_FIXTURE_DIR:-/tmp/acestream-fixture}"
MANIFEST="${ACESTREAM_MANIFEST:-/tmp/acestream-manifest.json}"
VENDOR_ROOT="${ACESTREAM_VENDOR_ROOT:-/tmp/acestream-vendor}"
SCRIPTS_DIR="${ACESTREAM_SCRIPTS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
SOURCE="${ACESTREAM_SOURCE:-auto}"
TARGET_PLATFORM="${TARGETPLATFORM:-}"

log() { printf 'install-acestream: %s\n' "$*"; }
fail() { printf 'install-acestream: %s\n' "$*" >&2; exit 1; }

mkdir -p "$ACE_DIR" "$ACE_BIN_DIR" "$SYS_DIR" "$SRC_DIR"

# ---------------------------------------------------------------------------
# Resolve what to install
# ---------------------------------------------------------------------------
case "$SOURCE" in
    fixture)
        ACESTREAM_INSTALL_KIND="executable"
        ACESTREAM_BINARY_PATH="${ACESTREAM_BINARY_PATH:-start-engine}"
        ACESTREAM_DOWNLOAD_URL=""
        ACESTREAM_VENDORED_FILE=""
        ;;
    explicit)
        if [ -z "${ACESTREAM_DOWNLOAD_URL:-}" ] && [ -z "${ACESTREAM_VENDORED_FILE:-}" ]; then
            fail "ACESTREAM_SOURCE=explicit needs ACESTREAM_DOWNLOAD_URL or ACESTREAM_VENDORED_FILE"
        fi
        ;;
    auto)
        [ -n "$TARGET_PLATFORM" ] || fail "TARGETPLATFORM is not set (pass --platform to docker buildx build)"
        [ -f "$MANIFEST" ] || fail "manifest not found: $MANIFEST"
        # Remember what the caller pinned explicitly: an explicit engine URL /
        # sha256 means "test this archive", so the manifest's vendored copy and
        # mirrors (which hold the *pinned* archive) must not shadow it.
        caller_url="${ACESTREAM_DOWNLOAD_URL:-}"
        caller_vendored="${ACESTREAM_VENDORED_FILE:-}"
        caller_mirrors="${ACESTREAM_MIRROR_URLS:-}"
        caller_bionic_url="${ACESTREAM_BIONIC_URL:-}"
        caller_bionic_vendored="${ACESTREAM_BIONIC_VENDORED_FILE:-}"
        caller_bionic_mirrors="${ACESTREAM_BIONIC_MIRROR_URLS:-}"
        if resolved="$(python3 "$SCRIPTS_DIR/acestream_manifest.py" "$MANIFEST" \
                --platform "$TARGET_PLATFORM" --format shell --respect-env 2>&1)"; then
            eval "$resolved"
            if [ -n "$caller_url" ]; then
                [ -n "$caller_vendored" ] || ACESTREAM_VENDORED_FILE=""
                [ -n "$caller_mirrors" ] || ACESTREAM_MIRROR_URLS=""
                log "explicit ACESTREAM_DOWNLOAD_URL given; not using the manifest's vendored engine copy or mirrors"
            fi
            if [ -n "$caller_bionic_url" ]; then
                [ -n "$caller_bionic_vendored" ] || ACESTREAM_BIONIC_VENDORED_FILE=""
                [ -n "$caller_bionic_mirrors" ] || ACESTREAM_BIONIC_MIRROR_URLS=""
                log "explicit ACESTREAM_BIONIC_URL given; not using the manifest's vendored bionic copy or mirrors"
            fi
        elif [ -n "${ACESTREAM_DOWNLOAD_URL:-}" ] || [ -n "${ACESTREAM_VENDORED_FILE:-}" ]; then
            log "$resolved"
            log "using explicit ACESTREAM_* values for $TARGET_PLATFORM"
        else
            fail "$resolved"
        fi
        ;;
    *)
        fail "unknown ACESTREAM_SOURCE=$SOURCE (expected auto, explicit or fixture)"
        ;;
esac

INSTALL_KIND="${ACESTREAM_INSTALL_KIND:-executable}"
ARCHIVE_TYPE="${ACESTREAM_ARCHIVE_TYPE:-tar.gz}"
STRIP_COMPONENTS="${ACESTREAM_STRIP_COMPONENTS:-1}"
BINARY_PATH="${ACESTREAM_BINARY_PATH:-acestreamengine}"
ENGINE_VERSION="${ACESTREAM_ENGINE_VERSION:-}"
PLATFORM_SUPPORT="${ACESTREAM_PLATFORM_SUPPORT:-stable}"
engine_source="fixture"
bionic_source=""

# ---------------------------------------------------------------------------
# Archive acquisition helpers
# ---------------------------------------------------------------------------
verify_sha256() {
    # verify_sha256 <file> <sha256|empty>
    local file="$1" expected="$2"
    if [ -z "$expected" ]; then
        log "WARNING: no sha256 pinned for $(basename "$file"); skipping verification"
        return 0
    fi
    printf '%s  %s\n' "$expected" "$file" | sha256sum -c - >/dev/null
}

fetch_verified() {
    # fetch_verified <dest> <vendor_subdir> <vendored_file> <sha256> <url> [mirror...]
    # Sets FETCHED_FROM on success.
    local dest="$1" subdir="$2" vendored="$3" sha="$4" url="$5"
    shift 5
    local candidate

    if [ -n "$vendored" ] && [ -f "$VENDOR_ROOT/$subdir/$vendored" ]; then
        cp "$VENDOR_ROOT/$subdir/$vendored" "$dest"
        if verify_sha256 "$dest" "$sha"; then
            FETCHED_FROM="vendored:$subdir/$vendored"
            log "using vendored $subdir/$vendored"
            return 0
        fi
        log "WARNING: vendored $subdir/$vendored does not match the pinned sha256; trying downloads"
        rm -f "$dest"
    fi

    for candidate in "$url" "$@"; do
        [ -n "$candidate" ] || continue
        log "downloading $candidate"
        if curl -fsSL --retry 3 --retry-delay 5 --connect-timeout 30 -o "$dest" "$candidate"; then
            if verify_sha256 "$dest" "$sha"; then
                FETCHED_FROM="$candidate"
                return 0
            fi
            log "WARNING: checksum mismatch for $candidate"
        else
            log "WARNING: download failed for $candidate"
        fi
        rm -f "$dest"
    done
    return 1
}

# ---------------------------------------------------------------------------
# Obtain the engine payload
# ---------------------------------------------------------------------------
ARCHIVE="$SRC_DIR/engine-archive"
if [ "$SOURCE" != "fixture" ]; then
    # shellcheck disable=SC2086  # mirror list is intentionally word-split
    if ! fetch_verified "$ARCHIVE" "${ACESTREAM_VENDOR_SUBDIR:-acestream}" \
            "${ACESTREAM_VENDORED_FILE:-}" "${ACESTREAM_DOWNLOAD_SHA256:-}" \
            "${ACESTREAM_DOWNLOAD_URL:-}" ${ACESTREAM_MIRROR_URLS:-}; then
        fail "could not obtain the AceStream engine archive from the vendored copy, the upstream URL or any mirror"
    fi
    engine_source="$FETCHED_FROM"
fi

# ---------------------------------------------------------------------------
# Install per kind
# ---------------------------------------------------------------------------
install_executable() {
    if [ "$SOURCE" = "fixture" ]; then
        cp -R "$FIXTURE_DIR/." "$ACE_DIR/"
    else
        case "$ARCHIVE_TYPE" in
            tar.gz)
                mkdir -p "$SRC_DIR/tree"
                tar -xzf "$ARCHIVE" -C "$SRC_DIR/tree" --strip-components="$STRIP_COMPONENTS"
                cp -R "$SRC_DIR/tree/." "$ACE_DIR/"
                ;;
            *)
                fail "unsupported ACESTREAM_ARCHIVE_TYPE=$ARCHIVE_TYPE for kind=executable"
                ;;
        esac
    fi

    case "$BINARY_PATH" in
        /*) resolved_binary="$BINARY_PATH" ;;
        *)  resolved_binary="$ACE_DIR/$BINARY_PATH" ;;
    esac
    if [ ! -f "$resolved_binary" ]; then
        fail "kind=executable but $resolved_binary is not a regular file"
    fi
    chmod +x "$resolved_binary"
    ln -sf "$resolved_binary" "$ACE_BIN_DIR/acestreamengine"

    # The 3.2.x tarball ships a requirements.txt for engine runtime deps;
    # pip-install it into a self-contained site-packages dir that the runtime
    # image puts on PYTHONPATH.
    if [ -f "$ACE_DIR/requirements.txt" ]; then
        PYTHON_VERSION="${ACESTREAM_PYTHON_VERSION:-3.10}"
        PYTHON_BIN="${ACESTREAM_PYTHON_BIN:-python${PYTHON_VERSION}}"
        if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
            fail "$PYTHON_BIN required to install requirements.txt but not found"
        fi
        mkdir -p "$ACE_DIR/python-deps"
        "$PYTHON_BIN" -m pip install \
            --no-warn-script-location \
            --target="$ACE_DIR/python-deps" \
            -r "$ACE_DIR/requirements.txt"
        # Fast-fail on ABI issues at build time rather than at first launch.
        PYTHONPATH="$ACE_DIR/python-deps" "$PYTHON_BIN" -c "import apsw; print('apsw ok')"
    fi
}

install_android_apk() {
    local abi="${ACESTREAM_ANDROID_ABI:-}"
    local libdir="${ACESTREAM_BIONIC_LIBDIR:-lib64}"
    local linker="${ACESTREAM_BIONIC_LINKER:-linker64}"
    local android_dir="$SCRIPTS_DIR/acestream-android"
    [ -n "$abi" ] || fail "kind=android-apk needs ACESTREAM_ANDROID_ABI (arm64-v8a or armeabi-v7a)"
    [ "$ARCHIVE_TYPE" = "apk" ] || fail "kind=android-apk expects ACESTREAM_ARCHIVE_TYPE=apk, got $ARCHIVE_TYPE"
    [ -d "$android_dir" ] || fail "Linux bootstrap files missing: $android_dir"
    command -v unzip >/dev/null 2>&1 || fail "unzip is required for kind=android-apk"
    command -v dpkg-deb >/dev/null 2>&1 || fail "dpkg-deb is required for kind=android-apk"

    # 1. Engine payload: the APK carries the python-for-android runtime and the
    #    engine as three zips under assets/engine/.
    local py_zip="assets/engine/${abi}_private_py.zip"
    local res_zip="assets/engine/${abi}_private_res.zip"
    local pub_zip="assets/engine/public_res.zip"
    mkdir -p "$SRC_DIR/apk"
    unzip -q -o "$ARCHIVE" "$py_zip" "$res_zip" "$pub_zip" -d "$SRC_DIR/apk" \
        || fail "APK does not contain the $abi engine payload ($py_zip)"
    unzip -q -o "$SRC_DIR/apk/$py_zip" -d "$ACE_DIR"
    unzip -q -o "$SRC_DIR/apk/$res_zip" -d "$ACE_DIR"
    unzip -q -o "$SRC_DIR/apk/$pub_zip" -d "$ACE_DIR"
    [ -f "$ACE_DIR/python/bin/python" ] || fail "engine payload has no python/bin/python launcher"
    [ -f "$ACE_DIR/main.py" ] || fail "engine payload has no main.py"
    chmod +x "$ACE_DIR/python/bin/python"

    # 2. Linux bootstrap: the APK's main.py/app_bridge.py expect the Android app
    #    as an RPC host and a /sdcard home. Keep the originals for reference.
    mv "$ACE_DIR/app_bridge.py" "$ACE_DIR/app_bridge.py.android-orig"
    mv "$ACE_DIR/acestream.conf" "$ACE_DIR/acestream.conf.android-orig"
    cp "$android_dir/app_bridge.py" "$ACE_DIR/app_bridge.py"
    cp "$android_dir/main_linux.py" "$ACE_DIR/main_linux.py"
    cp "$android_dir/acestream.conf" "$ACE_DIR/acestream.conf"
    cp "$android_dir/start-engine" "$ACE_DIR/start-engine"
    chmod +x "$ACE_DIR/start-engine"
    ln -sf "$ACE_DIR/start-engine" "$ACE_BIN_DIR/acestreamengine"

    # 3. Bionic userland (Android 9, Termux aosp-libs): the payload's ELF files
    #    hard-code PT_INTERP=/system/bin/<linker> and bare sonames.
    local deb="$SRC_DIR/aosp-libs.deb"
    # shellcheck disable=SC2086
    if ! fetch_verified "$deb" "${ACESTREAM_BIONIC_VENDOR_SUBDIR:-bionic}" \
            "${ACESTREAM_BIONIC_VENDORED_FILE:-}" "${ACESTREAM_BIONIC_SHA256:-}" \
            "${ACESTREAM_BIONIC_URL:-}" ${ACESTREAM_BIONIC_MIRROR_URLS:-}; then
        fail "could not obtain the bionic runtime package (aosp-libs)"
    fi
    bionic_source="$FETCHED_FROM"
    mkdir -p "$SRC_DIR/bionic"
    dpkg-deb -x "$deb" "$SRC_DIR/bionic"
    local aosp="$SRC_DIR/bionic/data/data/com.termux/files/usr/opt/aosp"
    local notices="$SRC_DIR/bionic/data/data/com.termux/files/usr/share/doc/aosp-libs"
    [ -f "$aosp/bin/$linker" ] || fail "aosp-libs package has no bin/$linker"
    mkdir -p "$SYS_DIR/bin" "$SYS_DIR/$libdir" "$SYS_DIR/etc/NOTICE-aosp-libs" "$SYS_DIR/usr/share/zoneinfo"
    cp "$aosp/bin/$linker" "$SYS_DIR/bin/"
    local lib
    for lib in ld-android libc libdl libm libz liblog libc++; do
        [ -f "$aosp/$libdir/$lib.so" ] || fail "aosp-libs package has no $libdir/$lib.so"
        cp "$aosp/$libdir/$lib.so" "$SYS_DIR/$libdir/"
    done
    # Android's tiny libstdc++ (operator new/delete, __cxa_*) is not shipped by
    # aosp-libs; libc++.so exports the same symbols.
    ln -sf libc++.so "$SYS_DIR/$libdir/libstdc++.so"
    cp "$aosp/usr/share/zoneinfo/tzdata" "$SYS_DIR/usr/share/zoneinfo/"
    # bionic resolves hostnames through /system/etc/hosts, not /etc/hosts.
    ln -sf /etc/hosts "$SYS_DIR/etc/hosts"
    cp "$notices"/NOTICE* "$SYS_DIR/etc/NOTICE-aosp-libs/" 2>/dev/null || true
    chmod 755 "$SYS_DIR/bin/$linker" "$SYS_DIR/$libdir"/*.so

    # 4. The engine forces pkg_resources to extract the pycountry egg into its
    #    own install dir at first start; do it now so a read-only or
    #    non-root runtime still works. Best effort: the runtime dir is
    #    writable in the shipped image anyway.
    (
        cd "$ACE_DIR" && python3 - <<'PY' || echo "install-acestream: WARNING: pycountry pre-extraction failed (non-fatal)" >&2
import glob, sys, warnings
warnings.simplefilter("ignore")
sys.path[:0] = sorted(glob.glob("eggs/pycountry-*.egg"))
import pkg_resources
pkg_resources.set_extraction_path("/opt/acestream")
import pycountry
pycountry.countries.get(alpha_2="LV")
print("install-acestream: pycountry egg pre-extracted")
PY
    )
    chmod -R a+rX "$ACE_DIR"
    resolved_binary="$ACE_DIR/start-engine"
}

case "$INSTALL_KIND" in
    executable)  install_executable ;;
    android-apk) install_android_apk ;;
    *) fail "unknown ACESTREAM_INSTALL_KIND=$INSTALL_KIND (expected executable or android-apk)" ;;
esac

rm -rf "$SRC_DIR"

printf 'platform=%s\nkind=%s\nengine_version=%s\nsupport=%s\nsource_url=%s\narchive_type=%s\nstrip_components=%s\nsha256=%s\nengine_source=%s\nabi=%s\nbionic_source=%s\nresolved_binary=%s\n' \
    "$TARGET_PLATFORM" \
    "$INSTALL_KIND" \
    "$ENGINE_VERSION" \
    "$PLATFORM_SUPPORT" \
    "${ACESTREAM_DOWNLOAD_URL:-}" \
    "$ARCHIVE_TYPE" \
    "$STRIP_COMPONENTS" \
    "${ACESTREAM_DOWNLOAD_SHA256:-}" \
    "$engine_source" \
    "${ACESTREAM_ANDROID_ABI:-}" \
    "$bionic_source" \
    "$resolved_binary" \
    > "$ACE_DIR/install-metadata.txt"
log "installed kind=$INSTALL_KIND for ${TARGET_PLATFORM:-unknown platform} from $engine_source"

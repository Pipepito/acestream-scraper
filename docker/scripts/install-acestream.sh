#!/usr/bin/env bash
# Installs AceStream into /opt/acestream from either a downloaded tarball
# (when ACESTREAM_DOWNLOAD_URL is set) or the docker/testdata fixture.
#
# Inputs (env / build-args):
#   ACESTREAM_DOWNLOAD_URL       Optional. If set, fetched and extracted.
#   ACESTREAM_DOWNLOAD_SHA256    Optional. If set, verified after download.
#   ACESTREAM_ARCHIVE_TYPE       Default tar.gz.
#   ACESTREAM_STRIP_COMPONENTS   Default 1.
#   ACESTREAM_INSTALL_KIND       executable | python_module. Default executable.
#   ACESTREAM_BINARY_PATH        For kind=executable: path inside extracted tree.
#                                Default acestreamengine.
#   ACESTREAM_PYTHON_MODULE      For kind=python_module: dotted module name.
#                                Default acestreamengine.
#   ACESTREAM_PYTHON_VERSION     For kind=python_module: e.g. "3.10". Informational.
#   ACESTREAM_FIXTURE_DIR        Where to copy the fixture from when URL is empty.
#                                Default /tmp/acestream-fixture.
#
# Output: /opt/acestream populated; /opt/acestream/bin/acestreamengine is an
# executable file (real binary or wrapper script). /opt/acestream/install-metadata.txt
# records source URL, kind, and resolved binary for diagnostics.

set -euo pipefail

ACE_DIR="/opt/acestream"
ACE_BIN_DIR="$ACE_DIR/bin"
SRC_DIR="/tmp/acestream-src"
FIXTURE_DIR="${ACESTREAM_FIXTURE_DIR:-/tmp/acestream-fixture}"
ARCHIVE_TYPE="${ACESTREAM_ARCHIVE_TYPE:-tar.gz}"
STRIP_COMPONENTS="${ACESTREAM_STRIP_COMPONENTS:-1}"
INSTALL_KIND="${ACESTREAM_INSTALL_KIND:-executable}"
BINARY_PATH="${ACESTREAM_BINARY_PATH:-acestreamengine}"

mkdir -p "$ACE_DIR" "$ACE_BIN_DIR" "$SRC_DIR"

if [ -n "${ACESTREAM_DOWNLOAD_URL:-}" ]; then
    curl -fsSL "$ACESTREAM_DOWNLOAD_URL" -o /tmp/acestream.tar.gz
    if [ -n "${ACESTREAM_DOWNLOAD_SHA256:-}" ]; then
        printf '%s  %s\n' "$ACESTREAM_DOWNLOAD_SHA256" /tmp/acestream.tar.gz | sha256sum -c -
    fi
    case "$ARCHIVE_TYPE" in
        tar.gz)
            tar -xzf /tmp/acestream.tar.gz -C "$SRC_DIR" --strip-components="$STRIP_COMPONENTS"
            ;;
        *)
            printf 'Unsupported ACESTREAM_ARCHIVE_TYPE: %s\n' "$ARCHIVE_TYPE" >&2
            exit 1
            ;;
    esac
    cp -R "$SRC_DIR/." "$ACE_DIR/"
else
    cp -R "$FIXTURE_DIR/." "$ACE_DIR/"
fi

case "$BINARY_PATH" in
    /*) resolved_binary="$BINARY_PATH" ;;
    *)  resolved_binary="$ACE_DIR/$BINARY_PATH" ;;
esac

case "$INSTALL_KIND" in
    executable)
        if [ ! -f "$resolved_binary" ]; then
            printf 'install-acestream: kind=executable but %s is not a regular file\n' \
                "$resolved_binary" >&2
            exit 1
        fi
        chmod +x "$resolved_binary"
        ln -sf "$resolved_binary" "$ACE_BIN_DIR/acestreamengine"
        ;;
    python_module)
        PYTHON_VERSION="${ACESTREAM_PYTHON_VERSION:-3.10}"
        PYTHON_BIN="${ACESTREAM_PYTHON_BIN:-python${PYTHON_VERSION}}"
        PY_MODULE="${ACESTREAM_PYTHON_MODULE:-acestreamengine}"
        TEMPLATE_PATH="${ACESTREAM_WRAPPER_TEMPLATE:-/usr/local/share/acestream/wrapper.sh.tpl}"

        if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
            printf 'install-acestream: %s not found in installer image\n' "$PYTHON_BIN" >&2
            exit 1
        fi

        # Verify the python package directory we expect actually exists.
        if [ ! -d "$ACE_DIR/$PY_MODULE" ]; then
            printf 'install-acestream: expected python package dir %s/%s\n' "$ACE_DIR" "$PY_MODULE" >&2
            exit 1
        fi

        # Install bundled wheels into a self-contained site-packages dir.
        # The tarball may bundle wheels for multiple architectures (e.g. x86_64
        # and s390x). Install each wheel individually, silently skipping any
        # that are not supported on this platform.
        mkdir -p "$ACE_DIR/site-packages"
        wheel_glob=("$ACE_DIR"/*.whl)
        if [ -e "${wheel_glob[0]}" ]; then
            for whl in "${wheel_glob[@]}"; do
                set +e
                pip_out=$("$PYTHON_BIN" -m pip install \
                    --no-deps \
                    --no-warn-script-location \
                    --target="$ACE_DIR/site-packages" \
                    "$whl" 2>&1)
                pip_rc=$?
                set -e
                if [ $pip_rc -ne 0 ]; then
                    if printf '%s' "$pip_out" | grep -qi 'not a supported wheel'; then
                        printf 'install-acestream: skipping incompatible wheel %s\n' "$(basename "$whl")"
                    else
                        printf '%s\n' "$pip_out" >&2
                        exit $pip_rc
                    fi
                fi
            done
        fi

        # Render the wrapper template.
        if [ ! -f "$TEMPLATE_PATH" ]; then
            printf 'install-acestream: wrapper template missing at %s\n' "$TEMPLATE_PATH" >&2
            exit 1
        fi
        sed \
            -e "s|__ACE_HOME__|$ACE_DIR|g" \
            -e "s|__PYTHON_BIN__|$PYTHON_BIN|g" \
            -e "s|__PY_MODULE__|$PY_MODULE|g" \
            "$TEMPLATE_PATH" > "$ACE_BIN_DIR/acestreamengine"
        chmod +x "$ACE_BIN_DIR/acestreamengine"
        resolved_binary="$ACE_BIN_DIR/acestreamengine"

        # Smoke import inside the installer image — fast-fail at build time
        # if the Python version / .so ABI is incompatible.
        LD_LIBRARY_PATH="$ACE_DIR" \
            PYTHONPATH="$ACE_DIR:$ACE_DIR/site-packages" \
            "$PYTHON_BIN" -c "import $PY_MODULE; print('imported', $PY_MODULE.__name__)"
        ;;
    *)
        printf 'install-acestream: unknown ACESTREAM_INSTALL_KIND=%s\n' "$INSTALL_KIND" >&2
        exit 1
        ;;
esac

printf 'source_url=%s\narchive_type=%s\nstrip_components=%s\nsha256=%s\nkind=%s\nresolved_binary=%s\n' \
    "${ACESTREAM_DOWNLOAD_URL:-}" \
    "$ARCHIVE_TYPE" \
    "$STRIP_COMPONENTS" \
    "${ACESTREAM_DOWNLOAD_SHA256:-}" \
    "$INSTALL_KIND" \
    "$resolved_binary" \
    > "$ACE_DIR/install-metadata.txt"

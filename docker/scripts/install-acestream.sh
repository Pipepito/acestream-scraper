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
        printf 'install-acestream: python_module install kind not yet implemented\n' >&2
        exit 1
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

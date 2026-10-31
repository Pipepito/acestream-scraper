#!/usr/bin/env bash
# Build-stage only: retain official WARP headless binaries and provenance.
# APT verifies the repository signature and package hashes before extraction.
set -euo pipefail
case "${TARGETARCH:?TARGETARCH required}" in
  amd64|arm64) ;;
  arm) exit 0 ;;
  *) echo "Unsupported WARP architecture" >&2; exit 1 ;;
esac
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl
. /etc/os-release
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
printf 'deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ %s main\n' "$VERSION_CODENAME" > /etc/apt/sources.list.d/cloudflare-client.list
apt-get update
mkdir -p /tmp/warp-package
cd /tmp/warp-package
apt-get download cloudflare-warp
packages=(cloudflare-warp_*.deb)
[[ ${#packages[@]} == 1 && -f "${packages[0]}" ]]
deb="${packages[0]}"
# Fail closed if the vendor adds an unreviewed runtime dependency.
# Only the three desktop-specific dependencies are deliberately omitted.
dpkg-deb -f "$deb" Depends | tr ',' '\n' | while read -r dependency; do
  name=$(printf '%s' "$dependency" | awk '{print $1}')
  case "$name" in
    libdbus-1-3|libc6|iproute2|nftables|gnupg2|libcap2-bin|libnss3-tools|ca-certificates|libpcap0.8|libtss2-esys-3.0.2-0t64|libtss2-tctildr0t64) ;;
    desktop-file-utils|libayatana-appindicator3-1|libwebkit2gtk-4.1-0) ;;
    *) echo "Review new WARP dependency: $name" >&2; exit 1 ;;
  esac
done
dpkg-deb -x "$deb" extracted
for tool in warp-cli warp-svc warp-dex warp-diag; do
  test -f "extracted/bin/$tool" && test ! -L "extracted/bin/$tool"
  install -m 0755 "extracted/bin/$tool" "/opt/warp-root/usr/bin/$tool"
done
cp -a extracted/usr/share/doc/cloudflare-warp/. /opt/warp-root/usr/share/doc/cloudflare-warp/
dpkg-deb -f "$deb" > /opt/warp-root/usr/share/doc/cloudflare-warp/package-control
sha256sum "$deb" > /opt/warp-root/usr/share/doc/cloudflare-warp/package-sha256

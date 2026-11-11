#!/bin/sh
# Inbound connections with WARP in tunnel mode (pipepito/acestream-scraper#93).
#
# WARP routes everything except its own marked packets through the tunnel
# (`ip rule`: "not from all fwmark <M> lookup <T>") and installs a firewall
# (`table inet cloudflare-warp`, input/output policy drop) that only lets in
# the tunnel, lo and private/excluded ranges. A client with a public address
# is dropped, and replies to it would go into the tunnel.
#
# 1) Connections that come in on eth0 are tagged with WARP's own mark, so its
#    own rule keeps their replies out of the tunnel wherever it puts that rule.
# 2) WARP rebuilds its firewall on every (re)connect: an accept for those
#    connections is put back into its input and output chains when missing.
#
# Only replies to connections that came in on that interface leave outside the
# tunnel. While WARP is down the kill switch (inet scraper_warp_guard) still
# rejects them, so inbound connections from public addresses wait for WARP.
#
# Tested 2026-10-19 with warp-cli 2026.8.2100.0: a client on a non-private
# subnet gets no answer without this script, and HTTP 200 with it, before and
# after three reconnects; other traffic stays on WARP (cdn-cgi/trace warp=on).
IFACE=${WARP_INBOUND_IFACE:-eth0}

mark=""
while [ -z "$mark" ]; do
  mark=$(ip rule list | sed -n 's/.*not from all fwmark \(0x[0-9a-f]*\) lookup.*/\1/p' | head -1)
  [ -n "$mark" ] || sleep 2
done
padded=$(printf '0x%08x' "$mark")

nft list table inet warp_inbound >/dev/null 2>&1 || {
  nft add table inet warp_inbound
  nft add chain inet warp_inbound pre "{ type filter hook prerouting priority mangle; }"
  nft add rule inet warp_inbound pre iifname "$IFACE" ct state new ct mark set "$mark"
  nft add chain inet warp_inbound out "{ type route hook output priority mangle; }"
  nft add rule inet warp_inbound out ct mark "$mark" meta mark set "$mark"
}

while :; do
  for chain in input output; do
    nft list chain inet cloudflare-warp "$chain" >/dev/null 2>&1 || continue
    nft list chain inet cloudflare-warp "$chain" | grep -q "ct mark $padded accept" ||
      nft insert rule inet cloudflare-warp "$chain" ct mark "$mark" accept
  done
  sleep 1
done

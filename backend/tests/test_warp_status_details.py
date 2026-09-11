"""WARP status must carry the IP and tunnel/registration details users can act on."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.services.warp_service import CLOUDFLARE_TRACE_URL, WarpService

TUNNEL_STATS = """Tunnel Protocol: MASQUE (HTTPS via UDP)
Endpoints: 162.159.198.2, ::
Time since last handshake: 658s
Sent: 2.8MB; Received: 14.2MB
Estimated latency: 11ms
Estimated loss: 0.00%
TLS Handshake:
\tVersion: TLSv1.3
\tPost-Quantum enabled: true
Colo: MAD (927f116)
"""

REGISTRATION = """Account type: Free
ID: 8898f66a-f6ae-4117-83ce-1c36690a6691
Device ID: 8898f66a-f6ae-4117-83ce-1c36690a6691
Public key: 3059301306
Account ID: bc7314f285bd482aab7b3b6c3c5ace21
License: Tz4K62g7-541A6SMm-36HvK92k
"""

TRACE = {"ip": "2a09:bac5:310f:245a::39f:74", "loc": "ES", "colo": "MAD", "warp": "on"}


def test_trace_url_has_no_trailing_slash():
    # /cdn-cgi/trace/ answers 404; the trace only works without the slash.
    assert CLOUDFLARE_TRACE_URL == "https://www.cloudflare.com/cdn-cgi/trace"


def test_parse_tunnel_stats_extracts_operator_facing_fields():
    stats = WarpService.parse_tunnel_stats(TUNNEL_STATS)
    assert stats["protocol"] == "MASQUE (HTTPS via UDP)"
    assert stats["endpoints"] == "162.159.198.2, ::"
    assert stats["last_handshake"] == "658s"
    assert stats["sent"] == "2.8MB"
    assert stats["received"] == "14.2MB"
    assert stats["latency"] == "11ms"
    assert stats["loss"] == "0.00%"
    assert stats["colo"] == "MAD"
    assert stats["tls_version"] == "TLSv1.3"


def test_parse_registration_masks_the_license():
    reg = WarpService.parse_registration(REGISTRATION)
    assert reg["account_type"] == "free"
    assert reg["account_id"] == "bc7314f285bd482aab7b3b6c3c5ace21"
    assert reg["device_id"] == "8898f66a-f6ae-4117-83ce-1c36690a6691"
    assert reg["license"] == "Tz4K…K92k"
    assert WarpService.parse_registration("Account type: Team\n")["account_type"] == "team"


def test_get_status_fills_ip_from_trace_and_reports_tunnel_details():
    service = WarpService()

    async def run_command(args):
        if args == ["status"]:
            return 0, "Status update: Connected\n", ""
        return 1, "", "unexpected"

    async def run_with_fallback(primary, _legacy):
        if primary == ["registration", "show"]:
            return 0, REGISTRATION, ""
        if primary == ["tunnel", "stats"]:
            return 0, TUNNEL_STATS, ""
        return 1, "", ""

    with patch.object(service, "_run_command", side_effect=run_command), \
         patch.object(service, "_run_with_fallback", side_effect=run_with_fallback), \
         patch.object(service, "get_mode", new=AsyncMock(return_value=None)), \
         patch.object(service, "get_cf_trace", new=AsyncMock(return_value=TRACE)):
        status = asyncio.run(service.get_status())

    assert status["connected"] is True
    assert status["ip"] == TRACE["ip"]
    assert status["location"] == "ES"
    assert status["colo"] == "MAD"
    assert status["tunnel"]["latency"] == "11ms"
    assert status["registration"]["device_id"] == "8898f66a-f6ae-4117-83ce-1c36690a6691"
    assert status["registration"]["license"] == "Tz4K…K92k"
    assert status["account_type"] == "free"
    assert status["cf_trace"] == TRACE

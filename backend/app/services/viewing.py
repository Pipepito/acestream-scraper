"""Whether someone is watching right now, so background work can wait.

The scheduled status pass opens the engine for every source it checks. On a
small box that ran next to the channel being watched: on 2026-10-14 the
hourly pass started at 21:49, in the middle of a match, and was still going
when the box was switched off at 22:58. The pass only skipped the one source
the relay was playing, not the others on the same engine.

Two ways of watching, each seen differently:

- the TV relay (/tuner/channel and /tuner/stream): its claim is in
  ``relay_registry`` from the request until the client leaves;
- the web player: its ``starting``/``ready`` sessions.
"""
from typing import Optional


def watching() -> Optional[str]:
    """What someone is watching through, or None when nobody is."""
    from app.services.recording_coordinator import recording_coordinator
    if recording_coordinator.activity():
        return "recording"
    from app.services.stream_relay import relay_registry
    if relay_registry.count_active():
        return "tv relay"
    from app.services.player_service import player_service
    if any(s.state in ("starting", "ready") for s in player_service.list_sessions()):
        return "web player"
    return None

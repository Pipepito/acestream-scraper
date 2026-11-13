"""Asynchronous startup observation; process ownership stays in the entrypoint."""
import asyncio
import os
import time

from warp_prerequisites import WarpStartupError
from warp_startup import StateError, Store


async def wait_for_warp(service, stopping: asyncio.Event, *, retry=False) -> bool:
    if os.environ.get('SCRAPER_WARP_STARTUP_ERROR'):
        service.startup_dependency = 'warp'
        raise WarpStartupError()
    if not os.environ.get('SCRAPER_WARP_BOOT'):
        return True
    service.startup_dependency = 'warp'
    try:
        store = Store.environment()
        if await asyncio.to_thread(store.released):
            service.startup_dependency = None
            return True
        request = await asyncio.to_thread(store.retry) if retry else None
        requested_at = time.monotonic()
        last_event = None
        while not stopping.is_set():
            if await asyncio.to_thread(store.released):
                service.startup_dependency = None
                return True
            state = await asyncio.to_thread(store.state)
            if request and state['window'] != request:
                # Give the entrypoint time to restart a failed coordinator.
                if time.monotonic() - requested_at > 10:
                    raise StateError('WARP retry was not acknowledged.')
            else:
                if state['phase'] == 'failed' or time.monotonic() - state['heartbeat'] > 10:
                    raise StateError('WARP startup stopped.')
            event = (state['window'], state['phase'], state['attempt'])
            if event != last_event:
                messages = {
                    'starting': 'Waiting for WARP. Automatic recovery is limited to ten minutes.',
                    'configuring': f"Configuring WARP (attempt {state['attempt']}). Network services are paused.",
                    'backoff': 'WARP is not ready. Retrying automatically; network services remain paused.',
                    'configured': 'WARP is configured. Starting network services.',
                    'failed': 'Requesting another WARP startup attempt.',
                }
                service.record(messages[state['phase']])
                last_event = event
            try:
                await asyncio.wait_for(stopping.wait(), timeout=0.5)
            except TimeoutError:
                pass
        return False
    except (StateError, OSError, KeyError) as exc:
        raise WarpStartupError() from exc

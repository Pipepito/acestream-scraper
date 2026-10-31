"""Bounded unicast fallback when Docker cannot receive mDNS announcements."""
import asyncio
import ipaddress
import json
import time
from uuid import UUID

import httpx
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.services.access_service import trusted_client
from app.services.cast_service import receiver_address
from app.services.remote_players.scan import default_scan_cidr


def scan_networks(request):
    """Infer small LANs from the verified client and local interfaces, never DNS."""
    import ifaddr
    networks = []
    client = request.client.host if request.client else None
    if client and trusted_client(request, [f'{client}/32' if ':' not in client else f'{client}/128']):
        networks.append(default_scan_cidr(client))
    for adapter in ifaddr.get_adapters():
        for address in adapter.ips:
            if isinstance(address.ip, str):
                # Container/VPN addresses are not a useful automatic LAN guess.
                parsed = ipaddress.ip_address(address.ip)
                if parsed in ipaddress.ip_network('172.16.0.0/12'):
                    continue
                networks.append(default_scan_cidr(address.ip))
    return list(dict.fromkeys(n for n in networks if n))[:3]


class CastScanner:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.last_scan = 0.0

    async def discover(self, request, discovery):
        if self.lock.locked() or time.monotonic() - self.last_scan < 30:
            return discovery.list()
        async with self.lock:
            self.last_scan = time.monotonic()
            networks = await run_in_threadpool(scan_networks, request)
            await run_in_threadpool(discovery.start)
            if not networks:
                # mDNS is still useful with IPv6 or a proxy-hidden client.
                await asyncio.sleep(2)
                if discovery.list():
                    return discovery.list()
                raise HTTPException(409, 'No home network could be detected. Docker may need host networking for TV discovery. A trusted proxy must preserve the client address.')
            self.last_scan = time.monotonic()
            slots = asyncio.Semaphore(32)
            async with httpx.AsyncClient(timeout=httpx.Timeout(1.5), trust_env=False, follow_redirects=False) as client:
                async def probe(host):
                    async with slots:
                        info = await device_info(client, host)
                        if info:
                            discovery.remember_unicast(info)
                # At most three /24s, 32 in flight, and a global deadline.
                async with asyncio.timeout(20):
                    tasks = [probe(str(host)) for cidr in networks for host in ipaddress.ip_network(cidr).hosts()]
                    await asyncio.gather(*tasks)
            return discovery.list()


async def device_info(client, host):
    """Accept only a positive Cast video identity, not an arbitrary open port."""
    from pychromecast.models import CastInfo, HostServiceInfo
    if not receiver_address(host):
        return None
    try:
        async with client.stream('GET', f'http://{host}:8008/setup/eureka_info?params=device_info,name', headers={'Accept-Encoding': 'identity'}) as response:
            if response.status_code != 200 or response.headers.get('content-encoding', 'identity') != 'identity':
                return None
            body = bytearray()
            async for chunk in response.aiter_raw(chunk_size=16385):
                body.extend(chunk)
                if len(body) > 16384:
                    return None
        data = json.loads(body)
        info = data.get('device_info', {})
        if info.get('capabilities', {}).get('display_supported') is not True:
            return None
        identity = UUID(info.get('ssdp_udn', '').removeprefix('uuid:'))
        name = str(info.get('name') or data.get('name') or 'TV')[:100]
        model = str(info.get('model_name') or '')[:100]
        return CastInfo({HostServiceInfo(host, 8009)}, identity, model, name, host, 8009, 'cast', 'Google')
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return None


cast_scanner = CastScanner()

"""Offline, real-node source bootstrap through a prefixed HTTP gateway.

Run --seed with the bundled ZeroNet interpreter, then the default mode with the
application interpreter after entrypoint has started the node. No public peers
or credentials are needed; the ephemeral signing key stays in memory.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import time

DATA = Path('/data/zeronet')
CHANNEL_ID = '1234567890abcdef1234567890abcdef12345678'


def seed():
    app = Path('/opt/zeronet/app')
    os.chdir(app)
    sys.path[:0] = [str(app), str(app / 'src'), str(app / 'src/lib')]
    sys.argv = ['zeronet.py', '--no-bootstrap', '--offline']
    from src.Config import config
    sys.modules['Config'] = sys.modules['src.Config']
    config.parse()
    from Crypt import CryptBitcoin
    private_key = CryptBitcoin.newPrivatekey()
    address = CryptBitcoin.privatekeyToAddress(private_key)
    site = DATA / address
    site.mkdir(parents=True)
    payload = json.dumps({'links': [{'name': 'Offline fixture', 'url': 'acestream://' + CHANNEL_ID}]}).encode()
    (DATA / 'fixture-links.json').write_bytes(payload)
    (site / 'index.html').write_text('<html>Offline fixture</html>')
    content = {'address': address, 'inner_path': 'content.json', 'title': 'Offline fixture',
               'modified': int(time.time()), 'files': {}}
    for name in ('links.json', 'index.html'):
        body = payload if name == 'links.json' else (site / name).read_bytes()
        content['files'][name] = {'sha512': hashlib.sha512(body).hexdigest()[:64], 'size': len(body)}
    content['signs'] = {address: CryptBitcoin.sign(json.dumps(content, sort_keys=True), private_key)}
    (site / 'content.json').write_text(json.dumps(content))
    (DATA / 'fixture-address').write_text(address)
    # Deliberately do not register the site: fetching links.json must first show
    # the node's add-site prompt, then the scraper requests its root to add it.


async def verify():
    import aiohttp
    from aiohttp import web
    address = (DATA / 'fixture-address').read_text()
    internal = 'http://127.0.0.1:43110'
    async with aiohttp.ClientSession() as session:
        for _ in range(150):
            try:
                async with session.get(internal + '/', timeout=aiohttp.ClientTimeout(total=1)) as response:
                    await response.read()
                    if response.status == 200:
                        break
            except (aiohttp.ClientError, TimeoutError):
                pass
            await asyncio.sleep(.1)
        else:
            raise AssertionError('Bundled ZeroNet did not start')
        async with session.get(internal + '/' + address + '/links.json') as response:
            assert 'name="add_nonce"' in await response.text(), 'fixture must start unregistered'
        requested = []
        async def forward(request):
            suffix = request.match_info['suffix']
            requested.append(suffix)
            async with session.get(internal + '/' + suffix, headers={'Accept': 'text/html,*/*'}) as response:
                body = await response.read()
                if suffix == address + '/' and response.status == 200:
                    # Deliver the already signed fixture after the real node has
                    # registered the site. P2P availability is deliberately outside
                    # this offline bootstrap/transport regression.
                    (DATA / address / 'links.json').write_bytes((DATA / 'fixture-links.json').read_bytes())
                return web.Response(body=body, status=response.status,
                                    headers={'Content-Type': response.headers.get('Content-Type', 'text/plain')})
        application = web.Application()
        application.router.add_get('/gateway/zero/{suffix:.*}', forward)
        runner = web.AppRunner(application)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        os.environ['ZERONET_URL'] = f'http://127.0.0.1:{port}/gateway/zero'
        try:
            from app.config.settings import get_settings
            get_settings.cache_clear()
            from app.models.url_types import ZeronetURL
            from app.scrapers.zeronet import ZeronetScraper
            url = 'zero://' + address + '/links.json'
            scraper = ZeronetScraper(ZeronetURL(url), timeout=3, retries=3)
            body = await scraper.fetch_content(url)
            assert scraper.channels_from_json(body) == [(CHANNEL_ID, 'Offline fixture', {})]
            assert address + '/' in requested, 'scraper must request the prefixed root to bootstrap'
            assert requested.count(address + '/links.json') >= 2
            print('PASS: fresh real ZeroNet node, root bootstrap, custom port/prefix and JSON channel import')
        finally:
            await runner.cleanup()


if __name__ == '__main__':
    if '--seed' in sys.argv:
        seed()
    else:
        asyncio.run(verify())

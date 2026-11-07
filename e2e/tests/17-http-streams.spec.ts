import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import type { AddressInfo } from 'node:net';
import { test, expect } from '../src/fixtures';

// Exercise the built backend's importer, bounded transport, ffprobe and public
// manifest route. The origin is local so CDN availability cannot mask a failure.
test('HTTP imports verify actual media and serve signed manifests with required headers', async ({ page, api, request }) => {
  test.setTimeout(120_000);
  const media = await readFile(path.resolve(__dirname, '../../backend/tests/docker/fixtures/sample-h264-ac3.m2ts'));
  const host = process.env.E2E_TARGET === 'docker' ? 'host.docker.internal' : '127.0.0.1';
  const referer = 'https://fixture.example/player';
  let origin = '';
  const server = createServer((req, res) => {
    const pathname = new URL(req.url ?? '/', 'http://fixture').pathname;
    if (pathname === '/sources.m3u') {
      res.end(`#EXTM3U\n#EXTINF:-1,E2E HTTP media\n#EXTVLCOPT:http-referrer=${referer}\n${origin}/master.m3u8\n#EXTINF:-1,E2E HTTP HTML\n#EXTVLCOPT:http-referrer=${referer}\n${origin}/html\n`);
      return;
    }
    if (req.headers.referer !== referer) { res.writeHead(403); res.end('Missing fixture Referer'); return; }
    if (pathname === '/master.m3u8') res.end('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\nsegments.m3u8\n');
    else if (pathname === '/segments.m3u8') res.end('#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXT-X-MEDIA-SEQUENCE:12\n#EXTINF:4,\nmedia.ts\n');
    else if (pathname === '/media.ts') { res.setHeader('Content-Type', 'video/mp2t'); res.end(media); }
    else if (pathname === '/html') { res.setHeader('Content-Type', 'text/html'); res.end('<html>Access denied</html>'); }
    else { res.writeHead(404); res.end(); }
  });
  await new Promise<void>(resolve => server.listen(0, '0.0.0.0', resolve));
  origin = `http://${host}:${(server.address() as AddressInfo).port}`;
  const mediaId = `url:${createHash('sha1').update(`${origin}/master.m3u8`).digest('hex')}`;
  const htmlId = `url:${createHash('sha1').update(`${origin}/html`).digest('hex')}`;
  let sourceId: number | undefined;
  const engine = await api.getSetting('ace_engine_url');
  try {
    await api.putSetting('ace_engine_url', '');
    const source = await api.createUrl({ url: `${origin}/sources.m3u`, url_type: 'regular' });
    sourceId = source.id;
    await api.triggerScrape(source.id);
    expect((await api.waitForScrape(source.url, null, 60_000)).status).toBe('OK');
    for (const [id, online] of [[mediaId, true], [htmlId, false]] as const) {
      const checked = await api.raw('post', `/api/v1/acestream-channels/${encodeURIComponent(id)}/check_status`);
      expect(checked.ok()).toBe(true);
      expect((await checked.json()).is_online).toBe(online);
      expect((await api.getChannel(id))?.is_online).toBe(online);
    }
    const playlist = await request.get('/playlist.m3u?only_online=false');
    expect(playlist.ok()).toBe(true);
    expect(await playlist.text()).toContain(`/live/${encodeURIComponent(mediaId)}|Referer=`);
    const master = await request.get(`/live/${encodeURIComponent(mediaId)}`);
    expect(master.ok()).toBe(true);
    const body = await master.text();
    expect(Number(master.headers()['content-length'])).toBe(Buffer.byteLength(body));
    const variant = body.split('\n').find(line => line.startsWith('/live/'));
    expect(variant).toContain('&s=');
    const chunklist = await request.get(variant!);
    expect(chunklist.ok()).toBe(true);
    expect(await chunklist.text()).toContain(`${origin}/media.ts`);
    const unsigned = await request.get(`/live/${encodeURIComponent(mediaId)}?u=http://169.254.169.254/latest`);
    expect(unsigned.status()).toBe(403);
    await page.goto('/acestream-channels');
    await expect(page.getByRole('heading', { name: 'Acestream Channels', exact: true })).toBeVisible();
  } finally {
    await api.putSetting('ace_engine_url', engine);
    if (sourceId !== undefined) await api.deleteUrl(sourceId);
    await api.deleteChannel(mediaId); await api.deleteChannel(htmlId);
    server.closeAllConnections();
    await new Promise<void>(resolve => server.close(() => resolve()));
  }
});

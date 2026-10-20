import { createServer } from 'node:http';
import { randomBytes } from 'node:crypto';
import { test, expect } from '../src/fixtures';
import { ScraperPage } from '../src/pages/scraper';
import { ChannelsPage } from '../src/pages/channels';

test('manual UI actions deliver one webhook each through the built backend', async ({ page, request, api }) => {
  const path = '/api/v1/config/notification_webhook_url';
  expect((await (await request.get(path)).json()).value, 'use a disposable E2E database').toBe('');
  const checker = await (await request.get('/api/v1/config/check-engine')).json();
  expect(checker.managed).toBe(false);
  const id = randomBytes(20).toString('hex');
  const name = `Notification fixture ${id.slice(0, 8)}`;
  const events: { event: string; data: Record<string, unknown> }[] = [];
  const server = createServer(async (req, res) => {
    if (req.method === 'POST') {
      const chunks: Buffer[] = [];
      for await (const chunk of req) chunks.push(Buffer.from(chunk));
      events.push(JSON.parse(Buffer.concat(chunks).toString()));
      res.end('{}');
    } else if (req.url?.startsWith('/source.m3u')) {
      res.setHeader('Content-Type', 'audio/x-mpegurl');
      res.end(`#EXTM3U\n#EXTINF:-1,${name}\nacestream://${id}\n`);
    } else {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(req.url?.startsWith('/server/api')
        ? { result: {} } : { error: 'content not found' }));
    }
  });
  await new Promise<void>((resolve) => server.listen(0, '0.0.0.0', resolve));
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('fixture server has no TCP port');
  const host = process.env.E2E_TARGET === 'docker' ? 'host.docker.internal' : '127.0.0.1';
  const origin = `http://${host}:${address.port}`;
  const source = `${origin}/source.m3u`;
  try {
    await page.goto('/settings?tab=automation');
    const section = page.getByRole('region', { name: 'Notifications', exact: true });
    await section.getByRole('textbox', { name: 'Webhook URL' }).fill(`${origin}/message?token=private`);
    await section.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'Notification webhook saved.' })).toBeVisible();
    await section.getByRole('button', { name: 'Send test', exact: true }).click();
    await expect.poll(() => events.map((event) => event.event)).toEqual(['test']);

    const scraper = new ScraperPage(page);
    await scraper.open();
    await scraper.addUrl({ url: source, urlType: 'regular' });
    await scraper.scrape(source);
    await expect.poll(() => events.map((event) => event.event)).toEqual(['test', 'url_scraping.completed']);
    expect(events[1].data).toEqual({ processed: 1, failures: 0, channels: 1 });
    await expect.poll(async () => (await api.getChannel(id))?.name).toBe(name);

    expect((await request.put('/api/v1/config/check-engine', {
      data: { use_dedicated: true, url: origin },
    })).ok()).toBe(true);
    const channels = new ChannelsPage(page);
    await channels.open();
    await channels.filterByName(name);
    await channels.checkStatus(name);
    // Earlier journeys start a real catalogue scan. A manual check has priority
    // but still waits for its current probe and cooldown to release the queue.
    await expect.poll(() => events.map((event) => event.event), {
      timeout: 90_000, message: 'queued manual check finishes and delivers its webhook',
    }).toEqual([
      'test', 'url_scraping.completed', 'channel_check.completed',
    ]);
    expect(events[2].data).toEqual({
      channel_id: id, status: 'offline', is_online: false, network_status: 'not_found',
    });
    expect(JSON.stringify(events)).not.toContain('private');
    expect(JSON.stringify(events)).not.toContain(source);
  } finally {
    await request.put(path, { data: { value: '' } });
    await request.put('/api/v1/config/check-engine', { data: { use_dedicated: checker.use_dedicated, url: checker.url } });
    const urls = await (await request.get('/api/v1/scrapers/urls')).json();
    for (const row of urls) if (row.url === source) await request.delete(`/api/v1/scrapers/urls/${row.id}`);
    await api.deleteChannel(id);
    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});

import path from 'node:path';
import { createServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import { test, expect } from '../src/fixtures';
import { startStubEngine } from '../src/stub-engine';

// Keep real HTTP, the built app, its scheduler and its player. Only engine
// responses are deterministic: no peer availability is needed to prove a pause.
// Run before catalogue ingestion so the complete pass covers only these seeds.
test('a scheduled check waits for watching to stop even with a dedicated checker', async ({ page, api }) => {
  test.setTimeout(240_000);
  const engineUrl = await api.getSetting('ace_engine_url');
  const routing = await api.raw('get', '/api/v1/config/playback-routing').then(r => r.json());
  const checker = await api.raw('get', '/api/v1/config/check-engine').then(r => r.json());
  expect(checker.managed).toBe(false);
  const network = process.env.E2E_TARGET === 'docker'
    ? { bindHost: '0.0.0.0', advertisedHost: 'host.docker.internal' }
    : { bindHost: '127.0.0.1', advertisedHost: '127.0.0.1' };
  const player = await startStubEngine(path.resolve(__dirname, '../../backend/tests/docker/fixtures/sample-h264-ac3.m2ts'), network);
  const probes: string[] = [];
  const checkServer = createServer((req, res) => {
    const url = new URL(req.url ?? '/', 'http://checker');
    res.setHeader('Content-Type', 'application/json');
    if (url.pathname === '/server/api') res.end(JSON.stringify({ result: {}, error: null }));
    else if (url.pathname === '/ace/getstream') {
      probes.push(url.searchParams.get('id') ?? url.searchParams.get('infohash') ?? '');
      res.end(JSON.stringify({ response: null, error: 'content not found' }));
    } else { res.statusCode = 404; res.end('{}'); }
  });
  await new Promise<void>(resolve => checkServer.listen(0, network.bindHost, resolve));
  const checkUrl = `http://${network.advertisedHost}:${(checkServer.address() as AddressInfo).port}`;
  const ids = ['e2e2390000000000000000000000000000000001', 'e2e2390000000000000000000000000000000002'];
  let tvId: number | undefined;
  const status = async () => (await api.backgroundTasks()).find(job => job.task_name === 'channel_status');
  const settled = async () => {
    const job = await status();
    return job?.status !== 'running' && job?.status !== 'waiting';
  };
  try {
    await expect.poll(settled, { timeout: 120_000 }).toBe(true);
    await api.putSetting('ace_engine_url', player.url);
    expect((await api.raw('put', '/api/v1/config/check-engine', { use_dedicated: true, url: checkUrl })).ok()).toBe(true);
    expect((await api.raw('put', '/api/v1/config/playback-routing', { use_acexy: false, acexy_url: routing.acexy_url })).ok()).toBe(true);
    for (const [i, id] of ids.entries()) await api.createChannel({ id, name: `E2E pause source ${i}` });
    const tv = await api.createTvChannel({ name: 'E2E pause watching' });
    tvId = tv.id;
    await api.associate(tv.id, ids[0]);
    await page.goto('/live-tv');
    await page.getByRole('button', { name: 'Watch E2E pause watching', exact: true }).click();
    const video = page.locator('video');
    await expect.poll(() => video.evaluate(v => (v as HTMLVideoElement).currentTime), { timeout: 60_000 }).toBeGreaterThan(1);
    const previousRun = (await status())?.last_run;
    expect((await api.raw('post', '/api/v1/background-tasks/channel_status/run')).ok()).toBe(true);
    await expect.poll(async () => (await status())?.status).toBe('running');
    await expect.poll(async () => (await status())?.last_run).not.toBe(previousRun);
    // Observe longer than the five-second pause poll, asserting throughout.
    const until = Date.now() + 6500;
    while (Date.now() < until) {
      expect(probes).toEqual([]);
      expect((await api.getChannel(ids[1]))?.last_checked).toBeNull();
      expect(await settled()).toBe(false);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    await page.getByRole('button', { name: 'Stop watching', exact: true }).click();
    await expect.poll(async () => Boolean((await api.getChannel(ids[1]))?.last_checked), { timeout: 90_000 }).toBe(true);
    await expect.poll(settled, { timeout: 90_000 }).toBe(true);
    expect(probes).toContain(ids[1]);
    expect((await status())?.last_result).toMatchObject({ failed: 0 });
    expect((await api.getChannel(ids[1]))?.is_online).toBe(false);
  } finally {
    await page.goto('/');
    await expect.poll(settled, { timeout: 120_000 }).toBe(true);
    await api.putSetting('ace_engine_url', engineUrl);
    await api.raw('put', '/api/v1/config/check-engine', { use_dedicated: checker.use_dedicated, url: checker.url });
    await api.raw('put', '/api/v1/config/playback-routing', routing);
    await player.close();
    checkServer.closeAllConnections();
    await new Promise<void>(resolve => checkServer.close(() => resolve()));
    if (tvId !== undefined) await api.deleteTvChannel(tvId);
    for (const id of ids) await api.deleteChannel(id);
  }
});

import path from 'node:path';
import { test, expect } from '../src/fixtures';
import { startStubEngine } from '../src/stub-engine';

test('video keeps advancing while browsing and switches channels inline', async ({ page, api }, testInfo) => {
  test.setTimeout(180_000);
  const caps = await api.raw('get', '/api/v1/player/capabilities').then(r => r.json());
  test.skip(!caps.ffmpeg_available, 'The application needs FFmpeg to prepare video.');
  const engineUrl = await api.getSetting('ace_engine_url');
  const routing = await api.raw('get', '/api/v1/config/playback-routing').then(r => r.json());
  const stub = await startStubEngine(path.resolve(__dirname, '../../backend/tests/docker/fixtures/sample-h264-ac3.m2ts'),
    process.env.E2E_TARGET === 'docker' ? { bindHost: '0.0.0.0', advertisedHost: 'host.docker.internal' } : undefined);
  const tvIds: number[] = [];
  const ids = ['e2e1000000000000000000000000000000000001', 'e2e1000000000000000000000000000000000002'];
  try {
    await api.putSetting('ace_engine_url', stub.url);
    await api.raw('put', '/api/v1/config/playback-routing', { use_acexy: false, acexy_url: routing.acexy_url });
    for (const [index, id] of ids.entries()) {
      await api.createChannel({ id, name: `E2E live source ${index + 1}` });
      const tv = await api.createTvChannel({ name: `E2E live TV ${index + 1}` });
      tvIds.push(tv.id);
      await api.associate(tv.id, id);
    }
    const starts: string[] = [];
    const leaves: string[] = [];
    page.on('request', request => {
      if (request.method() === 'POST' && request.url().endsWith('/player/sessions')) starts.push(request.postDataJSON().content_id);
      if (request.method() === 'DELETE' && request.url().includes('/player/sessions/')) leaves.push(request.url());
    });
    await page.goto('/live-tv');
    await page.getByRole('button', { name: 'Watch E2E live TV 1', exact: true }).click();
    const player = page.getByRole('region', { name: 'Live TV player', exact: true });
    await expect(player).toBeVisible();
    const video = page.locator('video');
    await expect.poll(() => video.evaluate(v => (v as HTMLVideoElement).currentTime), { timeout: 60_000 }).toBeGreaterThan(1);
    const before = await video.evaluate(v => (v as HTMLVideoElement).currentTime);
    await page.getByRole('searchbox', { name: 'Find a channel' }).fill('E2E live TV 2');
    await expect.poll(() => video.evaluate(v => (v as HTMLVideoElement).currentTime)).toBeGreaterThan(before + 2);
    expect(starts).toEqual([ids[0]]);
    expect(leaves).toHaveLength(0);
    await page.getByRole('button', { name: 'Watch E2E live TV 2', exact: true }).click();
    await expect.poll(() => starts).toEqual(ids);
    await expect.poll(() => leaves.length).toBe(1);
    await expect.poll(() => video.evaluate(v => (v as HTMLVideoElement).currentTime), { timeout: 60_000 }).toBeGreaterThan(1);
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(video).toBeInViewport();
    await expect(page.getByRole('searchbox', { name: 'Find a channel' })).toBeInViewport();
    await page.screenshot({ path: testInfo.outputPath('live-video-and-catalogue.png'), fullPage: true });
    await page.getByRole('button', { name: 'Stop watching', exact: true }).click();
    await expect(player).toHaveCount(0);
    await expect.poll(() => leaves.length).toBe(2);
    await expect.poll(() => stub.stopped(), { timeout: 45_000 }).toBe(true);
    await expect.poll(async () => {
      const result = await api.raw('get', '/api/v1/player/sessions').then(r => r.json());
      return result.sessions.filter((session: { content_id: string }) => ids.includes(session.content_id)).length;
    }, { timeout: 45_000, message: 'both test sessions were reaped after their viewers left' }).toBe(0);
  } finally {
    await page.goto('/');
    await api.putSetting('ace_engine_url', engineUrl);
    await api.raw('put', '/api/v1/config/playback-routing', routing);
    await stub.close();
    for (const id of tvIds) await api.deleteTvChannel(id);
    for (const id of ids) await api.deleteChannel(id);
  }
});

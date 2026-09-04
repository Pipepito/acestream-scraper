import { createServer, type Server } from 'node:http';
import path from 'node:path';
import type { AddressInfo } from 'node:net';
import { test, expect } from '../src/fixtures';
import { IntegrationsPage } from '../src/pages/integrations';
import { ChannelsPage } from '../src/pages/channels';
import { startStubEngine } from '../src/stub-engine';
import type { Api } from '../src/api';

test.describe.configure({ mode: 'serial' });

/** The app runs in a container for `npm run test:docker`, so loopback here is not loopback there. */
const IN_DOCKER = process.env.E2E_TARGET === 'docker';
const HOST_FROM_APP = IN_DOCKER ? 'host.docker.internal' : '127.0.0.1';
const TS_FIXTURE = path.resolve(__dirname, '..', '..', 'backend', 'tests', 'docker', 'fixtures', 'sample-h264-ac3.m2ts');

/** A VLC whose web interface has no password: it answers every request 403. */
async function startUnprotectedVlc(): Promise<{ port: number; close: () => Promise<void> }> {
  const server: Server = createServer((req, res) => {
    if ((req.url ?? '').startsWith('/requests/status.json')) {
      res.writeHead(403, { 'Content-Type': 'text/html' });
      res.end('<html><head><title>403 Forbidden</title></head><body><pre>Forbidden</pre></body></html>');
      return;
    }
    res.writeHead(404);
    res.end();
  });
  await new Promise<void>((resolve) => server.listen(0, '0.0.0.0', resolve));
  return {
    port: (server.address() as AddressInfo).port,
    close: () => new Promise<void>((resolve) => server.close(() => resolve())),
  };
}

/** The Acestream channel the playback checks use: the scenario's pick, else the first one. */
async function playbackChannel(api: Api, nameHint?: string): Promise<{ id: string; name: string }> {
  const page = await api.listChannels({ page_size: 100 });
  expect(page.items.length, 'earlier journeys imported channels to play').toBeGreaterThan(0);
  const preferred = nameHint ? page.items.find((c) => c.name.toLowerCase().includes(nameHint.toLowerCase())) : undefined;
  const chosen = preferred ?? page.items[0];
  return { id: chosen.id, name: chosen.name };
}

test.describe('integrations', () => {
  test('the page shows every integration section and the public address', async ({ page, api }) => {
    const integrations = new IntegrationsPage(page);
    await integrations.open();

    await expect(integrations.publicAddressSection()).toBeVisible();
    await expect(integrations.webPlayerSection()).toBeVisible();
    await expect(integrations.remotePlayersSection()).toBeVisible();
    await expect(integrations.mediaServersSection()).toBeVisible();

    const resolved = (await api.raw('get', '/api/v1/system/public-url').then((r) => r.json())) as { url: string };
    await expect(integrations.summary()).toContainText('Public address');
    await expect(integrations.summary()).toContainText(resolved.url);
    await expect(integrations.publicAddressSection()).toContainText(resolved.url);
  });

  test('a VLC without a password is diagnosed in plain words, and the player can be deleted again', async ({ page, errors }) => {
    const vlc = await startUnprotectedVlc();
    // Everything this test provokes upstream: the probe and the card's own status poll
    // both get 502 REMOTE_PLAYER_AUTH from a VLC with no password, and a poll already in
    // flight when the player is deleted lands on 404.
    errors.allowApi(/\/api\/v1\/remote-players\/test 502/);
    errors.allowApi(/\/api\/v1\/remote-players\/\d+\/status (502|404)/);
    const integrations = new IntegrationsPage(page);
    await integrations.open();

    const name = 'E2E unprotected VLC';
    try {
      await integrations.openAddPlayer({ name, kind: 'VLC (desktop)', host: HOST_FROM_APP, port: vlc.port });
      await integrations.testConnection();
      await integrations.expectProbe(/web interface has no password/i);

      await page.getByRole('dialog').getByRole('button', { name: 'Add player', exact: true }).click();
      await expect(integrations.playerCard(name)).toBeVisible();
      await integrations.deletePlayer(name);
    } finally {
      await vlc.close();
    }
  });

  test('the tuner answers its own routes and never the SPA', async ({ api }) => {
    const discover = await api.raw('get', '/tuner/discover.json');
    expect(discover.status()).toBe(200);
    expect(discover.headers()['content-type']).toContain('application/json');
    const device = (await discover.json()) as { ModelNumber: string; Manufacturer: string; BaseURL: string; LineupURL: string };
    expect(device.ModelNumber).toBe('HDTC-2US');
    expect(device.Manufacturer).toBe('Silicondust');
    expect(device.BaseURL).toMatch(/\/tuner$/);
    expect(device.LineupURL).toMatch(/\/tuner\/lineup\.json$/);

    const lineup = await api.raw('get', '/tuner/lineup.json');
    expect(lineup.status()).toBe(200);
    expect(Array.isArray(await lineup.json())).toBe(true);

    // A typo'd tuner path must not fall through to index.html: a tuner client cannot parse it.
    const unknown = await api.raw('get', '/tuner/nope');
    expect(unknown.status()).toBe(404);
    expect(unknown.headers()['content-type']).toContain('application/json');
    expect(await unknown.text()).not.toContain('<html');
  });

  test('a channel plays end to end against a deterministic engine', async ({ page, api, scenario, errors }, testInfo) => {
    const caps = (await api.raw('get', '/api/v1/player/capabilities').then((r) => r.json())) as { ffmpeg_available: boolean };
    if (!caps.ffmpeg_available) {
      testInfo.annotations.push({ type: 'skipped', description: 'no ffmpeg on this host; the web player cannot prepare a stream' });
      test.skip();
      return;
    }
    if (IN_DOCKER) {
      testInfo.annotations.push({ type: 'skipped', description: 'the stub engine listens on loopback, which the containerised app cannot reach' });
      test.skip();
      return;
    }

    const target = await playbackChannel(api, scenario.integrations.playbackChannelName);
    // hls.js reports recoverable buffer hiccups on the console; they are not app errors.
    errors.allowConsole(/mediaError|bufferStalledError|hlsError/i);
    const engineUrl = await api.getSetting('ace_engine_url');
    const stub = await startStubEngine(TS_FIXTURE);
    try {
      await api.putSetting('ace_engine_url', stub.url);
      const channels = new ChannelsPage(page);
      await channels.open();
      await channels.filterByName(target.name);
      await channels.playChannel(target.name);

      const dialog = page.getByRole('dialog', { name: target.name });
      await expect(dialog).toBeVisible();
      await expect(dialog.getByRole('status')).toHaveText('Playing', { timeout: scenario.integrations.playbackTimeoutMs });

      // "Playing" is the backend's word for it; readyState is the browser's.
      await expect
        .poll(() => page.evaluate(() => document.querySelector('video')?.readyState ?? 0), {
          timeout: 30_000,
          message: 'the <video> element buffered enough data to play',
        })
        .toBeGreaterThanOrEqual(2);

      expect(stub.streamCount(), 'the backend pulled the stream from the engine').toBeGreaterThan(0);
      await dialog.getByRole('button', { name: 'Close' }).click();
      await expect(dialog).toBeHidden();
      // Closing the dialog releases the session; the reaper then tells the engine to stop
      // (5 s without viewers, checked on a 5 s tick) — nothing should keep streaming.
      await expect
        .poll(() => stub.stopped(), { timeout: 45_000, message: 'closing the dialog stopped the engine stream' })
        .toBe(true);
      testInfo.annotations.push({ type: 'playback', description: `${target.name} played from the stub engine` });
    } finally {
      await api.putSetting('ace_engine_url', engineUrl);
      await stub.close();
    }
  });

  test('the same channel is attempted against the real engine', async ({ page, api, scenario }, testInfo) => {
    const caps = (await api.raw('get', '/api/v1/player/capabilities').then((r) => r.json())) as { ffmpeg_available: boolean };
    if (!caps.ffmpeg_available) {
      testInfo.annotations.push({ type: 'skipped', description: 'no ffmpeg on this host' });
      test.skip();
      return;
    }
    const target = await playbackChannel(api, scenario.integrations.playbackChannelName);
    const channels = new ChannelsPage(page);
    await channels.open();
    await channels.filterByName(target.name);
    await channels.playChannel(target.name);

    const dialog = page.getByRole('dialog', { name: target.name });
    await expect(dialog).toBeVisible();
    // A live channel depends on real peers, so both outcomes are legitimate: what
    // must never happen is a dialog that sits there saying nothing.
    const playing = dialog.getByRole('status').filter({ hasText: 'Playing' });
    const failed = dialog.getByRole('alert');
    await expect(playing.or(failed).first()).toBeVisible({ timeout: scenario.integrations.playbackTimeoutMs });
    const outcome = (await playing.count()) > 0 ? 'playing' : `error: ${(await failed.first().innerText()).replace(/\s+/g, ' ').slice(0, 200)}`;
    testInfo.annotations.push({ type: 'real-engine-playback', description: `${target.name} -> ${outcome}` });

    await dialog.getByRole('button', { name: 'Close' }).click();
    await expect(dialog).toBeHidden();
  });
});

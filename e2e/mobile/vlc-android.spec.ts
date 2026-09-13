import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: pair VLC Android and retain supported controls`, async ({ page }) => {
    const errors: string[] = [];
    const players: Record<string, unknown>[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.route('**/api/**', async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname.replace('/api/v1', '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [], recovery_token: 'test' };
      else if (path === '/system/public-url') data = { url: 'http://192.168.1.10:8000', source: 'setting', warnings: [] };
      else if (path === '/player/streams') data = { streams: [] };
      else if (path === '/player/capabilities') data = { ffmpeg_available: true, max_sessions: 3 };
      else if (path === '/media-servers' || path === '/base-urls') data = [];
      else if (path === '/remote-players/android/pair/start') {
        expect(request.postDataJSON()).toEqual({ host: '192.168.1.20', port: 8443 });
        data = { challenge: 'challenge', fingerprint: 'a'.repeat(64) };
      } else if (path === '/remote-players/android/pair/finish') {
        expect(request.postDataJSON()).toMatchObject({ code: '123456', challenge: 'challenge', fingerprint: 'a'.repeat(64) });
        data = { password: 'paired-credential' };
      } else if (path === '/remote-players') {
        if (request.method() === 'POST') {
          expect(request.postDataJSON()).toMatchObject({ kind: 'vlc_android', password: 'paired-credential', port: 8443 });
          players.push({ ...request.postDataJSON(), id: 1, has_password: true, password: undefined });
          data = players[0];
        } else data = players;
      } else if (path === '/remote-players/1/status') data = { state: 'playing', title: 'Arena', position_s: 2, volume_pct: 50 };
      else if (path === '/tuner/status') data = { channels: { total: 0, exposed: 0 }, warnings: [], network: { warnings: [], recent_denials: [], allowed_networks: [], client_allowed: true } };
      else if (path === '/tuner/settings') data = { tuner_allowed_networks: 'private', tuner_stream_buffer_mb: 8 };
      await route.fulfill({ json: data });
    });
    await page.goto('/integrations');
    await page.getByRole('button', { name: 'Add player', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByRole('textbox', { name: 'Name', exact: true }).fill('Android TV');
    await dialog.getByRole('combobox', { name: 'Player', exact: true }).click();
    await page.getByRole('option', { name: 'VLC Android (3.6+)' }).click();
    await dialog.getByRole('textbox', { name: 'Host', exact: true }).fill('192.168.1.20');
    await dialog.getByRole('button', { name: 'Request pairing code' }).click();
    await dialog.getByRole('textbox', { name: 'Pairing code' }).fill('123456');
    expect(await dialog.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`pairing-${mode}.png`), fullPage: true });
    await dialog.getByRole('button', { name: 'Pair with VLC Android' }).click();
    await expect(dialog.getByText(/Paired with VLC Android/)).toBeVisible();
    await dialog.getByRole('button', { name: 'Add player', exact: true }).click();
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Pause Android TV' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Stop Android TV' })).toHaveCount(0);
    await expect(page.getByRole('slider', { name: 'Volume Android TV' })).toHaveAttribute('aria-valuemax', '100');
    expect(errors).toEqual([]);
  });
}

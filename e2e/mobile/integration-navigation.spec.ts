import { test, expect } from '@playwright/test';

const setups = [
  ['public-address', 'Public address'], ['web-player', 'Web player'],
  ['tv-casting', 'TV casting'], ['remote-players', 'Remote players'], ['media-servers', 'Media servers'], ['telegram', 'Telegram'],
] as const;

for (const mode of ['light', 'dark']) {
  test(`${mode}: integrations have independent pages and a menu category`, async ({ page }) => {
    // This journey loads all six integrations plus their menu navigation.
    test.setTimeout(60_000);
    const errors: string[] = [];
    const requests: string[] = [];
    const mutations: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (['warning', 'error'].includes(message.type())) errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.addInitScript(value => {
      if (location.protocol !== 'about:') localStorage.setItem('app-theme-mode', value);
    }, mode);
    await page.route('**/api/**', route => {
      const request = route.request();
      const path = new URL(request.url()).pathname.replace('/api/v1', '').replace(/\/$/, '');
      requests.push(path);
      if (request.method() !== 'GET') mutations.push(path);
      const fixtures: Record<string, unknown> = {
        '/auth/status': { mode: 'open', user: null, permissions: [], csrf: 'fixture-csrf', legacy_token: false },
        '/cast/capabilities': { server_devices: true, home_connection: true, compatibility_conversion: false, media_url_configured: true, media_url: 'https://scraper.example.test' },
        '/cast/settings': { home_networks: [], remote_casting: false, compatibility_conversion: false, cast_media_url: '' },
        '/cast/devices': [{ id: 'tv', name: 'Living room television with a long descriptive name', model: 'Google Cast Android TV' }],
        '/startup': { status: 'ready', phase: 'Ready to use', events: [] },
        '/system/public-url': { url: 'http://scraper.test:8000', source: 'setting', warnings: [] },
        '/remote-players': [], '/media-servers': [], '/base-urls': [],
        '/player/streams': { streams: [] },
        '/player/capabilities': { ffmpeg_available: true, max_sessions: 3, ffmpeg_path: '/usr/bin/ffmpeg' },
        '/tuner/status': { warnings: [], recent_denials: [], urls: {}, channel_count: 0, overflow: 0 },
        '/tuner/settings': { friendly_name: 'TV tuner', tuner_count: 4, max_channels: 450, only_online: false, source_start_seconds: 15, startup_budget_seconds: 45, plex_compatible_audio: false, experimental_transcoding: false },
      };
      return route.fulfill({ json: fixtures[path] ?? {} });
    });
    for (const [slug, title] of setups) {
      // Unmount the previous SPA before measuring the next page. Its pending
      // queries otherwise race with clearing this request inventory in Firefox.
      await page.goto('about:blank');
      requests.length = 0;
      await page.goto(`/integrations/${slug}`);
      await expect(page.getByRole('heading', { level: 1, name: title, exact: true })).toBeVisible();
      await page.waitForLoadState('networkidle');
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      if (slug !== 'web-player') expect(requests).not.toContain('/player/streams');
      if (slug !== 'remote-players') expect(requests).not.toContain('/remote-players');
      if (slug !== 'media-servers') expect(requests).not.toContain('/media-servers');
      if (slug !== 'public-address') expect(requests).not.toContain('/system/public-url');
      expect(requests.some(path => path.includes('/telegram/'))).toBe(false);
      if (slug === 'tv-casting') {
        await expect(page.getByText('Living room television with a long descriptive name')).toBeVisible();
        await page.getByRole('button', { name: 'Advanced connection settings' }).click();
        await expect(page.getByRole('textbox', { name: 'Application address for TVs' })).toHaveValue('');
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      }
      if (slug === 'media-servers') {
        await page.getByRole('button', { name: 'Tuner settings', exact: true }).click();
        await expect(page.getByRole('textbox', { name: 'Tuner name' })).toBeVisible();
      }
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: test.info().outputPath(`${slug}-${mode}.png`), fullPage: true, animations: 'disabled' });
      const menu = page.getByRole('button', { name: 'open drawer' });
      if (await menu.isVisible()) await menu.click();
      const group = page.getByRole('list', { name: 'Integrations', exact: true });
      await expect(group.getByRole('link')).toHaveCount(6);
      await expect(group.getByRole('link', { name: title, exact: true })).toHaveAttribute('aria-current', 'page');
      await group.getByRole('link', { name: 'Public address', exact: true }).click();
      await expect(page).toHaveURL(/\/integrations\/public-address$/);
      await expect(page.getByRole('heading', { level: 1, name: 'Public address' })).toBeVisible();
      await page.waitForLoadState('networkidle');
    }
    await page.goto('/integrations');
    await expect(page).toHaveURL(/\/integrations\/public-address$/);
    await expect(page.getByRole('textbox', { name: 'Public address' })).toHaveValue('http://scraper.test:8000');
    expect(mutations).toEqual([]);
    expect(errors).toEqual([]);
  });
}

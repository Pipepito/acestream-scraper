import { test, expect } from '@playwright/test';

for (const theme of ['light', 'dark']) {
  test(`${theme}: stable categories and current genres navigate independently with logo fallback`, async ({ page }) => {
    const errors: string[] = [];
    const requests: URL[] = [];
    const writes: string[] = [];
    const asOf = new Date().toISOString();
    const channel = { id: 1, name: 'Example TV', category: 'general', category_id: 'general',
      category_origin: 'manual', category_revision: 1, logo_url: '/test-logo/saved.svg', epg_logo_url: '/test-logo/guide.svg',
      is_active: true, is_favorite: false, acestream_channels: [{ id: 'a'.repeat(40), name: 'Example stream', is_online: true, is_active: true }] };
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), theme);
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="#157565"/></svg>';
    await page.route('**/test-logo/saved.svg', route => route.fulfill({ contentType: 'image/svg+xml', body: 'invalid image' }));
    await page.route('**/test-logo/guide.svg', route => route.fulfill({ contentType: 'image/svg+xml', body: svg }));
    await page.route('**/api/**', route => {
      const request = route.request();
      const url = new URL(request.url());
      const path = url.pathname.replace('/api/v1', '');
      requests.push(url);
      if (request.method() !== 'GET') writes.push(path);
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [] };
      else if (path === '/tv-channels/categories') {
        const live = url.searchParams.get('category_basis') === 'now';
        data = { basis: live ? 'now' : 'channel', as_of: asOf, taxonomy_version: 1, total: 1,
          items: [{ id: live ? 'football' : 'general', label: live ? 'Football' : 'General TV', label_es: live ? 'Fútbol' : 'Generalista', artwork: live ? 'football' : 'entertainment', count: 1 }] };
      } else if (path === '/tv-channels/browse') data = { items: [channel], total: 1 };
      else if (path === '/tv-channels/now-next') data = [];
      else if (path === '/remote-players') data = [];
      else if (path === '/streams') data = { streams: [] };
      return route.fulfill({ json: data });
    });
    await page.goto('/live-tv');
    await expect(page.getByRole('button', { name: /General TV.*1 channel/ })).toBeVisible();
    await expect(page.getByRole('article')).toHaveCount(0);
    await page.getByRole('button', { name: /General TV.*1 channel/ }).click();
    await expect(page.getByRole('article', { name: 'Example TV', exact: true })).toBeVisible();
    const logo = page.getByRole('img', { name: 'Example TV', exact: true });
    await expect(logo).toHaveAttribute('src', '/test-logo/guide.svg');
    await expect.poll(() => logo.evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
    await page.getByRole('button', { name: 'On now', exact: true }).click();
    await expect(page.getByRole('button', { name: /Football.*1 channel/ })).toBeVisible();
    await page.getByRole('button', { name: /Football.*1 channel/ }).click();
    await expect(page.getByRole('article', { name: 'Example TV', exact: true })).toBeVisible();
    expect(requests.some(url => url.pathname.endsWith('/browse') && url.searchParams.get('category_id') === 'football'
      && url.searchParams.get('category_basis') === 'now' && url.searchParams.get('as_of') === asOf)).toBe(true);
    await page.getByRole('button', { name: 'Channel categories', exact: true }).click();
    await expect(page.getByRole('button', { name: /General TV.*1 channel/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Football.*1 channel/ })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  });
}

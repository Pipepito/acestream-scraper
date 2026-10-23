import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: Telegram source preview, save and pause remain usable`, async ({ page }) => {
    let saved: Record<string, unknown> | undefined;
    let source: Record<string, unknown> | undefined;
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.route('**/api/**', async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname.replace('/api/v1', '').replace(/\/$/, '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [] };
      else if (path === '/system/public-url') data = { url: 'http://scraper.test', source: 'request', warnings: [] };
      else if (path === '/remote-players' || path === '/media-servers' || path === '/base-urls') data = [];
      else if (path === '/player/streams') data = { streams: [] };
      else if (path === '/player/capabilities') data = { ffmpeg_available: true, max_sessions: 3 };
      else if (path === '/tuner/status') data = { warnings: [], recent_denials: [], urls: {}, channel_count: 0, renumbered: [], overflow: 0 };
      else if (path === '/telegram/status') data = { state: 'connected', account_label: 'Test account', message: '', queue_size: 0 };
      else if (path === '/telegram/chats') data = [{ id: '-100123', label: 'Sports group', kind: 'channel' }];
      else if (path === '/telegram/chats/-100123/topics') data = [];
      else if (path === '/telegram/preview') data = { chat_id: '-100123', messages: [{ message_id: 1, sender_id: '123', outcome: 'matched', result: { channels: [{ channel_id: 'a'.repeat(40), name: '🇪🇸 Campeones 🇻4️⃣' }], duplicate_count: 0, invalid_count: 0 } }] };
      else if (path === '/telegram/sources') {
        if (request.method() === 'POST') {
          saved = request.postDataJSON();
          source = { ...saved, id: 1, chat_label: 'Sports group', sender_labels: {}, cursor: 1, state: 'waiting', imported_count: 0, message: '' };
          data = source;
        } else data = source ? [source] : [];
      } else if (path === '/telegram/sources/1' && request.method() === 'PUT') {
        source = { ...source, ...request.postDataJSON(), state: 'paused' }; data = source;
      }
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');
    await page.getByLabel('Telegram admin token').fill('synthetic-admin-only');
    await page.getByRole('button', { name: 'Unlock Telegram settings' }).click();
    await page.getByRole('button', { name: 'Add Telegram source' }).click();
    await page.getByLabel('Source name').fill('Sports');
    await page.getByLabel('Joined chat').click();
    await page.getByRole('option', { name: 'Sports group (-100123)' }).click();
    await expect(page.getByLabel('Initial history count')).toHaveValue('0');
    await page.getByRole('button', { name: 'Test against recent messages' }).click();
    await expect(page.getByText(/🇪🇸 Campeones/)).toBeVisible();
    expect(saved).toBeUndefined();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`telegram-${mode}.png`), fullPage: true });
    await page.getByRole('button', { name: 'Save source' }).click();
    await expect.poll(() => saved?.chat_id).toBe('-100123');
    await page.getByRole('button', { name: 'Pause Sports' }).click();
    await expect(page.getByRole('button', { name: 'Resume Sports' })).toBeVisible();
    await page.getByRole('button', { name: 'Lock settings' }).click();
    await expect(page.getByLabel('Telegram admin token')).toHaveValue('');
    expect(await page.evaluate(() => JSON.stringify(localStorage))).not.toContain('synthetic-admin-only');
    expect(errors).toEqual([]);
  });
}

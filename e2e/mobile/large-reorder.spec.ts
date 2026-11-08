import { test, expect } from '@playwright/test';
import en from '../../frontend/src/i18n/messages/ui-en.json';
import es from '../../frontend/src/i18n/messages/ui-es.json';

for (const preset of ['lime', 'coral', 'cyan']) {
  for (const language of ['en', 'es'] as const) {
    for (const mode of ['light', 'dark']) {
      test(`${preset} ${language} ${mode}: complete large reorder keeps focus and saves every ID`, async ({ page }) => {
        const text = language === 'es' ? es : en;
        const original = Array.from({ length: 10000 }, (_, index) => index + 1);
        let order = [...original];
        const errors: string[] = [], writes: string[] = [];
        const payloads: { channel_ids: number[]; expected_order: number[] }[] = [];
        const channel = (id: number, index: number) => ({ id, name: `Synthetic channel ${String(id).padStart(5, '0')}`, channel_number: index + 1, is_active: true, is_favorite: false, acestream_channels: [] });
        const handleName = (id: number) => text['Drag {{value0}}'].replace('{{value0}}', channel(id, 0).name);
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => { if (['warning', 'error'].includes(message.type())) errors.push(message.text()); });
        await page.addInitScript(values => {
          localStorage.setItem('app-interface-v1', values.preset);
          localStorage.setItem('app-language-v1', values.language);
          localStorage.setItem('app-theme-mode', values.mode);
        }, { preset, language, mode });
        await page.route('**/api/**', async route => {
          const request = route.request(), url = new URL(request.url()), path = url.pathname.replace(/\/$/, '');
          if (!['GET', 'HEAD'].includes(request.method())) writes.push(path);
          let data: unknown = {};
          if (path.endsWith('/startup')) data = { status: 'ready', phase: 'Ready', events: [] };
          else if (path.endsWith('/setup')) data = { setup_complete: true, restart_required: false };
          else if (path.endsWith('/tv-channels/reorder')) {
            const payload = request.postDataJSON();
            payloads.push(payload);
            order = payload.channel_ids;
            data = { updated: order.length };
          } else if (path.endsWith('/tv-channels/inventory')) data = { total: order.length, favorites: 0, with_streams: 0, categories: [], countries: [], languages: [], epg_sources: [] };
          else if (path.endsWith('/tv-channels') || path.endsWith('/tv-channels/browse')) {
            const start = Number(url.searchParams.get('skip') ?? 0), count = Number(url.searchParams.get('limit') ?? 50);
            data = { total: order.length, items: order.slice(start, start + count).map((id, index) => channel(id, start + index)) };
          } else if (path.endsWith('/sources') || path.endsWith('/remote-players')) data = [];
          return route.fulfill({ json: data });
        });
        await page.goto('/tv-channels');
        await page.getByRole('button', { name: text['Reorder channels'], exact: true }).click();
        const list = page.getByRole('list', { name: text['Channel order'], exact: true });
        const first = page.getByRole('button', { name: handleName(1), exact: true });
        await expect(first).toBeVisible();
        if ((page.viewportSize()?.width ?? 1000) <= 390) {
          // An ordinary 23-character name must remain readable beside controls,
          // not wrap a few letters per line despite technically fitting the page.
          const name = list.getByText(channel(1, 0).name, { exact: true });
          expect(await name.evaluate(node => node.getBoundingClientRect().height / parseFloat(getComputedStyle(node).lineHeight))).toBeLessThanOrEqual(2.1);
        }
        expect(await list.getByRole('listitem').count()).toBeLessThan(40);
        await first.focus();
        await first.press('End');
        const last = page.getByRole('button', { name: handleName(10000), exact: true });
        await expect(last).toBeFocused();
        await expect(last).toBeVisible();
        await last.press('ArrowUp');
        const moved = list.getByRole('listitem').filter({ has: last });
        await expect(moved).toHaveAttribute('aria-posinset', '9999');
        await expect(moved).toHaveAttribute('aria-setsize', '10000');
        await expect(last).toBeFocused();
        expect(order).toEqual(original);
        await last.press('Home');
        await expect(first).toBeFocused();
        await first.press('PageDown');
        await expect(page.getByRole('button', { name: handleName(11), exact: true })).toBeFocused();
        expect(await list.getByRole('listitem').count()).toBeLessThan(40);
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
        await list.locator('..').screenshot({ path: test.info().outputPath('large-order.png') });
        await page.getByRole('button', { name: text['Save order'], exact: true }).click();
        await expect(list).toBeHidden();
        const expected = [...original.slice(0, 9998), 10000, 9999];
        expect(payloads).toEqual([{ channel_ids: expected, expected_order: original }]);
        expect(order).toEqual(expected);
        expect(writes).toEqual(['/api/v1/tv-channels/reorder']);
        // WebKit reports unused preloads several seconds after load. Observe
        // beyond that window once per browser instead of letting a fast pass
        // close the context before a late bundle warning can surface.
        if (preset === 'cyan' && language === 'en' && mode === 'light') await page.waitForTimeout(6500);
        expect(errors).toEqual([]);
      });
    }
  }
}

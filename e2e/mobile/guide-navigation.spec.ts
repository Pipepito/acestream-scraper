import { test, expect } from '@playwright/test';

for (const preset of ['lime', 'coral', 'cyan']) {
  for (const language of ['en', 'es']) {
    for (const mode of ['light', 'dark']) {
      test(`${preset} ${language} ${mode}: guide section labels fit and remain keyboard reachable`, async ({ page }) => {
        const errors: string[] = [];
        const writes: string[] = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
        await page.route('**/api/**', route => {
          const request = route.request();
          const path = new URL(request.url()).pathname;
          if (!['GET', 'HEAD'].includes(request.method())) writes.push(path);
          let data: unknown = {};
          if (path.endsWith('/startup')) data = { status: 'ready', phase: 'Ready', events: [] };
          else if (path.endsWith('/setup')) data = { setup_complete: true, restart_required: false };
          else if (path.endsWith('/sources') || path.endsWith('/mappings') || path.endsWith('/groups')) data = [];
          else if (path.endsWith('/channels') || path.endsWith('/tv-channels/')) data = { items: [], total: 0 };
          return route.fulfill({ json: data });
        });
        await page.addInitScript(({ preset, language, mode }) => {
          localStorage.setItem('app-interface-v1', preset);
          localStorage.setItem('app-language-v1', language);
          localStorage.setItem('app-theme-mode', mode);
        }, { preset, language, mode });
        await page.goto('/epg?tab=export');
        await page.evaluate(() => document.fonts.ready);
        const list = page.getByRole('tablist');
        const tabs = list.getByRole('tab');
        await expect(tabs).toHaveCount(5);
        await expect(tabs.last()).toHaveAttribute('aria-selected', 'true');
        const labelsFit = await tabs.evaluateAll(nodes => nodes.every(node => {
          const tab = node as HTMLElement;
          const bounds = tab.getBoundingClientRect();
          const viewport = tab.closest('[role="tablist"]')!.getBoundingClientRect();
          return bounds.left >= viewport.left - 1 && bounds.right <= viewport.right + 1
            && tab.scrollWidth <= tab.clientWidth + 1;
        }));
        expect(labelsFit).toBe(true);
        await tabs.last().focus();
        await page.keyboard.press('Home');
        await expect(tabs.first()).toBeFocused();
        await page.keyboard.press('End');
        await expect(tabs.last()).toBeFocused();
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
        await list.screenshot({ path: test.info().outputPath('guide-sections.png') });
        expect(errors).toEqual([]);
        expect(writes).toEqual([]);
      });
    }
  }
}

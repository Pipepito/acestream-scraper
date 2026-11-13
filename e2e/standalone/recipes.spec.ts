import { readFile } from 'node:fs/promises';
import { test, expect } from '@playwright/test';
import templates from '../../frontend/src/recipes/catalogue.json';
import en from '../../frontend/src/i18n/messages/ui-en.json';
import es from '../../frontend/src/i18n/messages/ui-es.json';

const escape = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
for (const language of ['en', 'es'] as const) {
  for (const mode of ['light', 'dark'] as const) {
    for (const width of [320, 390, 1440]) {
      test(`${language} ${mode} ${width}: templates and exports work without an installation`, async ({ page, baseURL }) => {
        const text = language === 'es' ? es : en;
        const errors: string[] = [];
        const forbidden: string[] = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => { if (['warning', 'error'].includes(message.type())) errors.push(message.text()); });
        await page.setViewportSize({ width, height: 900 });
        await page.emulateMedia({ colorScheme: mode });
        await page.addInitScript(value => localStorage.setItem('recipe-language-v1', value), language);
        await page.route('**/*', route => {
          const url = new URL(route.request().url());
          if (['http:', 'https:'].includes(url.protocol) && (url.origin !== new URL(baseURL!).origin || url.pathname.includes('/api/'))) {
            forbidden.push(url.href);
            return route.abort();
          }
          return route.continue();
        });
        await page.goto(baseURL!);
        await expect(page.locator('html')).toHaveAttribute('lang', language);
        for (const entry of templates) {
          await page.getByRole('combobox', { name: new RegExp(`^${escape(text['Recipe catalogue'])}`) }).click();
          await page.getByRole('option', { name: `${entry.recipe.name} · v${entry.recipe.version}`, exact: true }).click();
          await page.getByRole('button', { name: text['Load template and sample'], exact: true }).click();
          await page.getByRole('button', { name: text['Test sample'], exact: true }).click();
          for (const channel of entry.expected) {
            await expect(page.getByRole('cell', { name: channel.name, exact: true })).toBeVisible();
            await expect(page.getByRole('cell', { name: channel.channel_id, exact: true })).toBeVisible();
          }
          const download = page.waitForEvent('download');
          await page.getByRole('button', { name: text['Export recipe'], exact: true }).click();
          const file = await (await download).path();
          expect(JSON.parse(await readFile(file!, 'utf8'))).toEqual(entry.recipe);
          expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
        }
        await page.screenshot({ path: test.info().outputPath(`${language}-${mode}-${width}.png`), fullPage: true });
        expect(errors).toEqual([]);
        expect(forbidden).toEqual([]);
      });
    }
  }
}

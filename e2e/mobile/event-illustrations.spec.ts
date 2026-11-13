import { test, expect } from '@playwright/test';

for (const preset of ['lime', 'coral', 'cyan']) for (const language of ['en', 'es']) for (const mode of ['light', 'dark']) {
  test(`${preset} ${language} ${mode}: generic sport images stay separate from requested event artwork`, async ({ page }) => {
    const events = ['Football', 'Tennis'].map((sport, index) => ({ id: String(index + 1).repeat(32), revision: 1,
      title: `${sport} fixture`, sport, competition: 'Original competition', timezone: 'Europe/Madrid', starts_at: '2030-10-24T21:30:00Z',
      ends_at: null, state: 'scheduled', corrected: false, followed: false, archived: false, participants: [], time_notes: '',
      broadcasts: [], provenance: [], has_artwork: true }));
    let artworkRequests = 0;
    const writes: string[] = [];
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', route => {
      const { pathname } = new URL(route.request().url());
      if (route.request().method() !== 'GET') writes.push(pathname);
      if (pathname.endsWith('/artwork')) { artworkRequests++; return route.fulfill({ status: 404, json: { detail: 'fixture artwork absent' } }); }
      let json: unknown = {};
      if (pathname.endsWith('/startup')) json = { status: 'ready', phase: 'Ready', events: [] };
      else if (pathname.endsWith('/setup')) json = { setup_complete: true };
      else if (pathname === '/api/v1/events') json = { events, total: events.length };
      else if (events.some(event => pathname.endsWith(event.id))) json = events.find(event => pathname.endsWith(event.id));
      else if (pathname.endsWith('/sources') || pathname.endsWith('/broadcast-targets') || pathname.endsWith('/broadcaster-links')) json = [];
      else if (pathname.endsWith('/retention')) json = { ended_days: 0, archived_days: 0 };
      return route.fulfill({ json });
    });
    await page.addInitScript(({ preset, language, mode }) => {
      localStorage.setItem('app-interface-v1', preset);
      localStorage.setItem('app-language-v1', language);
      localStorage.setItem('app-theme-mode', mode);
    }, { preset, language, mode });
    await page.goto('/events');
    for (const [index, event] of events.entries()) {
      await page.getByRole('button', { name: language === 'es' ? `Ver emisiones de ${event.title}` : `View broadcasts for ${event.title}` }).click();
      const dialog = page.getByRole('dialog', { name: language === 'es' ? 'Detalles del evento' : 'Event details' });
      const caption = language === 'es' ? `Ilustración genérica de ${index === 0 ? 'fútbol' : 'tenis'}` : `Generic ${index === 0 ? 'football' : 'tennis'} illustration`;
      await expect(dialog.getByText(caption, { exact: true })).toBeVisible();
      const illustration = dialog.locator('figure img');
      await illustration.scrollIntoViewIfNeeded();
      await expect.poll(() => illustration.evaluate((node: HTMLImageElement) => node.naturalWidth)).toBeGreaterThan(0);
      expect(artworkRequests).toBe(index);
      await dialog.getByRole('button', { name: language === 'es' ? 'Cargar imagen del evento' : 'Load event artwork' }).click();
      await expect.poll(() => artworkRequests).toBe(index + 1);
      await expect(dialog.getByRole('button', { name: language === 'es' ? 'Reintentar imagen' : 'Retry artwork' })).toBeVisible();
      await expect(dialog.getByText(caption, { exact: true })).toBeAttached();
      expect(await dialog.evaluate(node => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
      await dialog.screenshot({ path: test.info().outputPath(`${event.sport.toLowerCase()}.png`) });
      await page.getByRole('button', { name: language === 'es' ? 'Cerrar detalles del evento' : 'Close event details' }).click();
    }
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  });
}

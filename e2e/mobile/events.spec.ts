import { test, expect } from '@playwright/test';

const fixture = {
  id: 'a'.repeat(32), revision: 1, title: 'North United vs South City — International championship final',
  sport: 'Football', competition: 'Example Cup', timezone: 'Europe/Madrid', starts_at: '2026-10-24T21:30:00Z',
  ends_at: null, state: 'scheduled', corrected: false, followed: false, archived: false, participants: [], time_notes: '',
  broadcasts: [
    { id: 'es', label: 'Sports One', language: 'Spanish', quality: 'HD', country: 'Spain', source_name: 'Example guide', origin: '', content_id: 'a'.repeat(40), compatibility: 'playable', reason: 'AceStream', is_online: null, checked_at: null },
    { id: 'unknown', label: 'DAZN', language: '', quality: '', country: '', source_name: 'Example guide', origin: '', content_id: null, compatibility: 'unresolved', reason: 'No stream mapped.', is_online: null, checked_at: null },
    { id: 'web', label: 'Publisher website', language: '', quality: '', country: '', source_name: 'Example guide', origin: 'player.example', content_id: null, compatibility: 'unsupported', reason: 'A compatible resolver is required.', is_online: null, checked_at: null },
  ],
  provenance: [{ source_id: 'guide', source_name: 'Example guide', source_kind: 'guide', external_id: '1', updated_at: '2026-10-22T00:00:00Z' }],
};
for (const mode of ['light', 'dark']) {
  test(`${mode}: event schedule, details and reviewed manual import`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    let applied = 0;
    let mapped = false;
    let retained = false;
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      let json: unknown = { status: 'ready', phase: 'Ready to use', events: [] };
      if (path === '/api/v1/events/sources') json = [];
      if (path === '/api/v1/events/broadcast-targets') json = [];
      if (path === '/api/v1/events/retention') {
        json = { ended_days: 0, archived_days: 0 };
        if (route.request().method() === 'PATCH') { retained = true; json = route.request().postDataJSON(); }
      }
      if (path === '/api/v1/acestream-channels/') json = { items: [{ id: 'b'.repeat(40), name: 'DAZN Spain', group: 'Spain', is_active: true }], total: 1 };
      if (path === `/api/v1/events/${fixture.id}/broadcast`) { mapped = true; json = fixture; }
      if (path === '/api/v1/events') json = { events: [fixture], total: 1 };
      if (path === `/api/v1/events/${fixture.id}`) json = fixture;
      if (path === '/api/v1/events/preview') json = { token: 'preview', events: [fixture], warnings: ['Import is not proof of live play or media signal.'] };
      if (path === '/api/v1/events/apply') { applied++; json = [fixture]; }
      await route.fulfill({ json });
    });
    await page.addInitScript(value => {
      localStorage.setItem('app-theme-mode', value);
      localStorage.setItem('acestream.changelog.seen.v1', 'v2.2.0');
    }, mode);
    await page.goto('/events');
    await expect(page.getByRole('heading', { name: 'Events', exact: true })).toBeVisible();
    const title = page.getByRole('button', { name: `View broadcasts for ${fixture.title}`, exact: true });
    await title.focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('button', { name: 'Play Sports One' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Play DAZN' })).toHaveCount(0);
    await expect(page.getByText('Link a channel to watch this broadcast.', { exact: true })).toBeVisible();
    await expect(page.getByRole('dialog', { name: 'Event details' })).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`event-details-${mode}.png`), fullPage: false, animations: 'disabled' });
    await page.getByRole('button', { name: 'Link DAZN', exact: true }).click();
    await page.getByRole('combobox', { name: /^Link to/ }).click();
    await page.getByRole('option', { name: 'Individual stream', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Save broadcast mapping' })).toBeDisabled();
    await page.getByRole('combobox', { name: 'Find stream for DAZN' }).click();
    await page.getByRole('option', { name: 'DAZN Spain · Spain · bbbbbbbb' }).click();
    await page.getByRole('button', { name: 'Save broadcast mapping' }).click();
    await expect.poll(() => mapped).toBe(true);
    await page.getByRole('button', { name: 'Close event details' }).click();
    await expect(page.getByRole('button', { name: 'Add events', exact: true })).toBeVisible();
    await page.getByRole('combobox', { name: /^When/ }).click();
    await page.getByRole('option', { name: 'Choose a date', exact: true }).click();
    await expect(page.getByLabel('Event date', { exact: true })).toBeVisible();
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: test.info().outputPath(`events-${mode}.png`), fullPage: true, animations: 'disabled' });
    await page.getByRole('button', { name: 'Add events', exact: true }).click();
    await page.getByRole('combobox', { name: /^Add from/ }).click();
    await page.getByRole('option', { name: 'Create an event', exact: true }).click();
    await page.getByLabel('Event title').fill('Another match');
    await page.getByRole('button', { name: 'Preview events', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Save selected (0)', exact: true })).toBeDisabled();
    expect(applied).toBe(0);
    await page.getByRole('checkbox', { name: `${fixture.title} · scheduled`, exact: true }).check();
    await page.getByRole('button', { name: 'Save selected (1)', exact: true }).click();
    await expect(page.getByRole('region', { name: 'Add events' })).toHaveCount(0);
    expect(applied).toBe(1);
    await page.getByRole('button', { name: 'Sources & retention', exact: true }).click();
    await page.getByLabel('Keep ended events (days)').fill('7');
    await page.getByRole('button', { name: 'Save retention' }).click();
    await expect.poll(() => retained).toBe(true);
    await expect(page.getByText('Retention saved. Changes take effect during daily maintenance.')).toBeVisible();
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: test.info().outputPath(`event-sources-${mode}.png`), fullPage: true, animations: 'disabled' });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(errors).toEqual([]);
  });
}

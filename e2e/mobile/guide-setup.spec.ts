import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: review guide matches and explicitly enable automation`, async ({ page }) => {
    let enabled = false;
    let applied: unknown;
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.route('**/api/**', async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname.replace('/api/v1', '').replace(/\/$/, '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [] };
      else if (path === '/playlists/guide-coverage') data = { streams: 20, linked_streams: applied ? 1 : 0, guide_channels: 3 };
      else if (path === '/playlists/groups' || path === '/base-urls') data = [];
      else if (path === '/system/public-url') data = { url: 'http://scraper.test', source: 'request', warnings: [] };
      else if (path === '/epg/sources') data = [{ id: 1, name: 'Reviewed guide', enabled: true, url: 'https://example.test/guide' }];
      else if (path === '/epg/channels' || path === '/tv-channels') data = { items: [], total: 0 };
      else if (path === '/tv-channels/analyze-epg-matches') data = {
        summary: { epg_channels_analyzed: 1, matched_epg_channels: 1, matched_acestream_channels: 1, creatable_rows: 1, skipped_existing_tv_channels: 0 },
        rows: [{ epg_channel_id: 1, epg_channel_xml_id: 'news', epg_channel_name: 'News One', epg_source_id: 1, epg_source_name: 'Reviewed guide',
          candidate_count: 1, candidates: [{ acestream_channel_id: 'a'.repeat(40), name: 'News One HD', match_stage: 'name_exact', score: 1 }],
          best_match_type: 'name_exact', best_match_confidence: 'high', is_creatable: true, can_apply: true, automation_safe: true, review_token: 'review-snapshot', ambiguous_count: 0 }],
      };
      else if (path === '/tv-channels/create-from-epg-analysis') {
        applied = request.postDataJSON();
        data = { created_count: 1, associated_count: 1, skipped_count: 0, failure_count: 0, row_outcomes: [] };
      } else if (path === '/config/epg-matching') {
        if (request.method() === 'PUT') enabled = request.postDataJSON().enabled;
        data = { enabled };
      } else if (path === '/config/epg-matching/last-run') data = { status: 'never' };
      else if (path === '/config/schedule-anchors') data = { timezone: 'UTC' };
      else if (path === '/config/check-engine') data = { use_dedicated: false, url: '', managed: false };
      else if (path === '/config/playback-routing') data = { use_acexy: false, acexy_url: 'http://localhost:8080' };
      else if (path === '/config/acestream_status') data = { status: 'online', message: 'Engine online' };
      else if (path === '/config/rescrape_interval' || path === '/config/epg_refresh_interval') data = { value: '6' };
      else if (path === '/config/channel_status_interval') data = { value: '60' };
      else if (path.startsWith('/config/')) data = { value: 'false' };
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/playlist');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('0 of 20 streams in your catalogue have a linked guide.')).toBeVisible();
    await page.getByRole('link', { name: 'Review guide matches' }).click();
    await expect(page.getByRole('tab', { name: 'Matching', exact: true })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('button', { name: 'Analyze Matches' }).click();
    const select = page.getByRole('checkbox', { name: 'select match row News One', exact: true });
    await expect(select).not.toBeChecked();
    await expect(page.getByText('News One HD', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Apply reviewed matches' })).toBeDisabled();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`guide-review-${mode}.png`), fullPage: true });
    await select.check();
    await page.getByRole('button', { name: 'Apply reviewed matches' }).click();
    await expect.poll(() => applied).toEqual({ strictness: 'strict', epg_channel_ids: [1], expected_previews: { 1: 'review-snapshot' } });
    await expect(page.getByText('Created 1 TV channels, assigned 1 streams, skipped 0')).toBeVisible();
    await page.goto('/settings?tab=automation');
    const automation = page.getByRole('checkbox', { name: 'Automatically match guide channels' });
    await expect(automation).not.toBeChecked();
    await automation.focus();
    await page.keyboard.press('Space');
    await expect.poll(() => enabled).toBe(true);
    await page.reload();
    await expect(automation).toBeChecked();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`guide-automation-${mode}.png`), fullPage: true });
    expect(errors).toEqual([]);
  });
}

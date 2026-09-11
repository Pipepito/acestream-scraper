import { test, expect } from '../src/fixtures';

test('optional checker settings persist and no-engine setups skip checks', async ({ page, api }) => {
  const playback = await (await api.raw('get', '/api/v1/config/ace_engine_url')).json();
  const checker = await (await api.raw('get', '/api/v1/config/check-engine')).json();
  test.skip(checker.managed, 'Bundled checker is controlled by the container.');
  try {
    await api.raw('put', '/api/v1/config/check-engine', { use_dedicated: false, url: '' });
    await page.goto('/settings?tab=automation');
    const form = page.getByRole('form', { name: 'Checking engine', exact: true });
    await form.getByRole('checkbox', { name: 'Use a dedicated checking engine' }).check();
    await form.getByRole('textbox', { name: 'Checking engine URL' }).fill(playback.value || 'http://127.0.0.1:6878');
    await form.getByRole('button', { name: 'Save checking engine', exact: true }).click();
    await expect(form.getByRole('alert')).toHaveText('Checking engine settings saved.');
    await page.reload();
    await expect(form.getByRole('checkbox')).toBeChecked();
    await form.getByRole('checkbox').uncheck();
    await form.getByRole('button', { name: 'Save checking engine', exact: true }).click();
    await expect(form.getByRole('alert')).toHaveText('Checking engine settings saved.');
    await page.getByRole('tab', { name: 'Playback', exact: true }).click();
    await page.getByRole('textbox', { name: 'Acestream Engine URL', exact: true }).fill('');
    await page.getByRole('button', { name: 'Save engine URL', exact: true }).click();
    await expect(page.getByRole('status', { name: 'Engine status', exact: true })).toContainText('Not configured');
    await page.goto('/');
    await expect(page.getByRole('status', { name: 'Overview summary' })).toContainText('not configured');
    const checkerCard = page.getByRole('group', { name: 'Service AceStream checking engine' });
    await expect(checkerCard).toContainText('Disabled');
    await expect(checkerCard.getByRole('link', { name: 'Configure engine' })).toHaveAttribute('href', '/settings?tab=automation');
    await page.screenshot({ path: 'test-results/optional-engines-overview.png', fullPage: true });
    await page.goto('/acestream-channels');
    await page.getByRole('button', { name: 'Run status check now', exact: true }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'No engine configured.' })).toBeVisible();
  } finally {
    expect((await api.raw('put', '/api/v1/config/ace_engine_url', { value: playback.value })).ok()).toBe(true);
    expect((await api.raw('put', '/api/v1/config/check-engine', { use_dedicated: checker.use_dedicated, url: checker.url })).ok()).toBe(true);
  }
});

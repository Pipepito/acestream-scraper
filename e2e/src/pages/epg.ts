import { expect, type Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class EPGPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/epg');
    await this.expectHeading('EPG Management');
  }

  sources(): Locator {
    return this.region('Source Operations');
  }

  sourceRow(name: string): Locator {
    return this.sources().getByRole('row').filter({ hasText: name });
  }

  async addSource(name: string, url: string, enabled = true): Promise<void> {
    await this.sources().getByRole('button', { name: 'Add EPG Source' }).click();
    const dialog = this.dialog('Add EPG Source');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('textbox', { name: 'Name' }).fill(name);
    await dialog.getByRole('textbox', { name: 'URL' }).fill(url);
    if (!enabled) await dialog.getByRole('checkbox', { name: 'Enabled' }).uncheck();
    await dialog.getByRole('button', { name: 'Add', exact: true }).click();
    await expect(dialog).toBeHidden();
  }

  async refreshSource(name: string): Promise<void> {
    await this.sourceRow(name).getByRole('button', { name: `Refresh source ${name}` }).click();
  }

  async openEditSource(name: string): Promise<Locator> {
    await this.sourceRow(name).getByRole('button', { name: `Edit source ${name}` }).click();
    const dialog = this.dialog('Edit EPG Source');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async deleteSource(name: string): Promise<void> {
    this.acceptNextDialog();
    await this.sourceRow(name).getByRole('button', { name: `Delete source ${name}` }).click();
  }

  async refreshAll(): Promise<void> {
    await this.sources().getByRole('button', { name: 'Refresh All' }).click();
  }

  matching(): Locator {
    return this.region('Channel Matching');
  }

  inventory(): Locator {
    return this.region('Channel Inventory');
  }

  async selectSourceFilter(name: string | RegExp): Promise<void> {
    await this.selectOption(this.page.getByRole('combobox', { name: /^EPG Source/ }), name);
  }

  async analyze(strictness: 'Loose' | 'Balanced' | 'Strict' = 'Balanced'): Promise<void> {
    await this.selectOption(this.page.getByRole('combobox', { name: /^Match Strictness/ }), strictness);
    await this.matching().getByRole('button', { name: 'Analyze Matches' }).click();
  }

  inventoryRow(name: string): Locator {
    return this.inventory().getByRole('row').filter({ hasText: name });
  }

  async viewPrograms(name: string): Promise<void> {
    await this.inventoryRow(name).getByRole('button', { name: `View programs for ${name}` }).click();
  }

  xmlOutput(): Locator {
    return this.region('XML Output');
  }
}

export class EPGChannelDetailPage extends AppShell {
  async open(id: number, name: string | RegExp): Promise<void> {
    await this.goto(`/epg/channels/${id}`);
    await this.expectHeading(name);
  }

  schedule(): Locator {
    return this.region('Program Schedule');
  }

  programsTable(): Locator {
    return this.page.getByRole('table', { name: 'Program schedule table' });
  }

  mappings(): Locator {
    return this.region('String Mapping Rules');
  }

  async mapToTvChannel(tvName: string): Promise<void> {
    await this.page.getByRole('button', { name: 'Map to TV Channel' }).click();
    const dialog = this.dialog('Map to TV Channel');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('radio', { name: new RegExp(`^${tvName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`) }).check();
    await dialog.getByRole('button', { name: 'Map Channel' }).click();
    await expect(dialog).toBeHidden();
  }

  async addStringMapping(pattern: string, exclusion = false): Promise<void> {
    await this.mappings().getByRole('button', { name: 'Add String Mapping' }).click();
    const dialog = this.dialog('Add String Mapping');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('textbox', { name: 'Search Pattern' }).fill(pattern);
    if (exclusion) await dialog.getByRole('checkbox', { name: 'Is Exclusion Pattern' }).check();
    await dialog.getByRole('button', { name: 'Add Mapping' }).click();
    await expect(dialog).toBeHidden();
  }

  async deleteStringMapping(pattern: string): Promise<void> {
    this.acceptNextDialog();
    await this.mappings().getByRole('button', { name: `Delete string mapping ${pattern}` }).click();
  }

  async createTvChannel(overrides: { name?: string; category?: string } = {}): Promise<void> {
    await this.page.getByRole('button', { name: 'Create TV Channel' }).click();
    const dialog = this.dialog('Create TV Channel from EPG');
    await expect(dialog).toBeVisible();
    if (overrides.name) await dialog.getByRole('textbox', { name: 'Channel Name' }).fill(overrides.name);
    if (overrides.category) await dialog.getByRole('textbox', { name: 'Category' }).fill(overrides.category);
    await dialog.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(dialog).toBeHidden();
  }

  /** The detail page snackbar never auto-hides; close it so later assertions do not see stale alerts. */
  async closeSnackbar(): Promise<void> {
    const close = this.page.getByRole('alert').getByRole('button', { name: 'Close' });
    if (await close.count()) await close.first().click();
  }
}

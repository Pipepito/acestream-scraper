import { expect, type Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class ChannelsPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/acestream-channels');
    await this.expectHeading('Acestream Channels');
  }

  grid(): Locator {
    return this.page.getByRole('grid');
  }

  dataRows(): Locator {
    return this.grid().locator('[role="row"][data-id]');
  }

  row(name: string): Locator {
    return this.grid().getByRole('row').filter({ hasText: name });
  }

  summary(): Locator {
    return this.statusLine('Channel summary');
  }

  filterBar(): Locator {
    return this.page.getByRole('search', { name: 'Channel filters' });
  }

  /** The search box is debounced; wait until the summary reports the filtered count. */
  async filterByName(text: string): Promise<void> {
    await this.filterBar().getByRole('textbox', { name: 'Search' }).fill(text);
    await expect(this.summary()).toContainText(/Matching filters\s*\d+/);
  }

  async resetFilters(): Promise<void> {
    await this.filterBar().getByRole('button', { name: 'Reset filters' }).click();
    await expect(this.summary()).toContainText(/Matching filters\s*all/);
  }

  async openEdit(name: string): Promise<Locator> {
    await this.rowMenuAction(this.row(name).first(), name, 'Edit');
    const dialog = this.dialog('Edit channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async openAdd(): Promise<Locator> {
    await this.headerButton('Add channel').click();
    const dialog = this.dialog('Add channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async checkStatus(name: string): Promise<void> {
    await this.row(name).first().getByRole('button', { name: `check channel status ${name}` }).click();
  }

  async checkAllStatuses(): Promise<void> {
    await this.headerButton(/Check all statuses|Checking/).click();
  }

  async deleteChannel(name: string): Promise<void> {
    await this.rowMenuAction(this.row(name).first(), name, 'Delete');
    await this.confirmDialog(`Delete ${name}?`, 'Delete');
  }

  async hideFromPlaylist(name: string): Promise<void> {
    await this.rowMenuAction(this.row(name).first(), name, 'Hide from playlist');
  }

  async showInPlaylist(name: string): Promise<void> {
    await this.rowMenuAction(this.row(name).first(), name, 'Show in playlist');
  }

  async openAssignTv(name: string): Promise<Locator> {
    await this.rowMenuAction(this.row(name).first(), name, 'Link to a TV channel');
    const dialog = this.dialog('Assign to TV Channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async playChannel(name: string): Promise<void> {
    await this.row(name).first().getByRole('button', { name: `play channel ${name}` }).click();
  }

  /** The TV link lives in the row menu; assert it and close the menu again. */
  async expectLinkedTv(name: string, tvName: string): Promise<void> {
    await this.row(name).first().getByRole('button', { name: `More actions for ${name}` }).click();
    await expect(this.page.getByRole('menuitem', { name: `Open TV channel: ${tvName}` })).toBeVisible();
    await this.page.keyboard.press('Escape');
  }

  csvButton(): Locator {
    return this.headerButton('Export CSV');
  }

  async refresh(): Promise<void> {
    await this.headerButton('Refresh').click();
  }

  onlineChip(name: string): Locator {
    return this.row(name).locator('[data-field="is_online"]');
  }
}

export function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

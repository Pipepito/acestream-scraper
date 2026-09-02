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

  row(name: string): Locator {
    return this.grid().getByRole('row').filter({ hasText: name });
  }

  filtersForm(): Locator {
    return this.page.getByRole('form', { name: 'Channel filters' });
  }

  async filterByName(text: string): Promise<void> {
    const form = this.filtersForm();
    await form.getByRole('textbox', { name: 'Search' }).fill(text);
    await form.getByRole('button', { name: 'Apply Filters' }).click();
  }

  async resetFilters(): Promise<void> {
    await this.filtersForm().getByRole('button', { name: 'Reset Filters' }).click();
  }

  async openEdit(name: string): Promise<Locator> {
    await this.row(name).getByRole('button', { name: `edit channel ${name}` }).click();
    const dialog = this.dialog('Quick Edit Channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async openAdd(): Promise<Locator> {
    await this.page.getByRole('button', { name: 'Add', exact: true }).click();
    const dialog = this.dialog('Quick Edit Channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async checkStatus(name: string): Promise<void> {
    await this.row(name).getByRole('button', { name: `check channel status ${name}` }).click();
  }

  async checkAllStatuses(): Promise<void> {
    await this.page.getByRole('button', { name: /Check All Statuses|Checking\.\.\./ }).click();
  }

  async deleteChannel(name: string): Promise<void> {
    this.acceptNextDialog();
    await this.row(name).getByRole('button', { name: `delete channel ${name}` }).click();
  }

  async toggleActive(name: string): Promise<void> {
    await this.row(name).getByRole('button', { name: new RegExp(`^(de)?activate channel ${escapeRegExp(name)}$`) }).click();
  }

  async openAssignTv(name: string): Promise<Locator> {
    await this.row(name).getByRole('button', { name: `assign tv channel to ${name}` }).click();
    const dialog = this.dialog('Assign to TV Channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  csvButton(): Locator {
    return this.page.getByRole('button', { name: 'CSV', exact: true });
  }

  async refresh(): Promise<void> {
    await this.page.getByTestId('page-header-actions').getByRole('button', { name: 'Refresh', exact: true }).click();
  }

  onlineChip(name: string): Locator {
    return this.row(name).locator('[data-field="is_online"]');
  }
}

export function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

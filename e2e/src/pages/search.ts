import type { Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class SearchPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/search');
    await this.expectHeading('Search Channels');
  }

  async search(query: string, category?: string): Promise<void> {
    await this.page.getByRole('textbox', { name: 'Search Query' }).fill(query);
    if (category) {
      await this.selectOption(this.comboboxByFormLabel('Category'), category);
    }
    await this.page.getByRole('button', { name: 'Search', exact: true }).click();
  }

  results(): Locator {
    return this.region('Search Results');
  }

  resultRows(): Locator {
    return this.results().getByRole('row').filter({ has: this.page.getByRole('button', { name: /^Add / }) });
  }

  resultRow(name: string): Locator {
    return this.results().getByRole('row').filter({ hasText: name });
  }

  async addRow(name: string): Promise<void> {
    await this.resultRow(name).getByRole('button', { name: `Add ${name}`, exact: true }).click();
  }

  async selectRow(name: string): Promise<void> {
    await this.resultRow(name).getByRole('checkbox', { name: `select search result ${name}` }).check();
  }

  async addSelected(): Promise<void> {
    await this.page.getByRole('button', { name: /^Add \d+ selected channels?$/ }).click();
  }

  errorAlert(): Locator {
    return this.page.getByRole('alert').filter({ hasText: /failed/ });
  }
}

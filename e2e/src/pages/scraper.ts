import { expect, type Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export interface AddUrlOptions {
  url: string;
  urlType?: 'auto' | 'regular' | 'zeronet' | 'ipfs';
  enabled?: boolean;
  bareIds?: boolean;
}

const URL_TYPE_LABEL = { auto: 'Auto-detect', regular: 'Regular HTTP', zeronet: 'ZeroNet', ipfs: 'IPFS' } as const;

export class ScraperPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/scraper');
    await this.expectHeading('Scraper');
  }

  sources(): Locator {
    return this.region('Sources');
  }

  status(): Locator {
    return this.statusLine('Source status');
  }

  row(url: string): Locator {
    return this.sources().getByRole('row').filter({ hasText: url });
  }

  async addUrl(opts: AddUrlOptions): Promise<void> {
    await this.headerButton('Add URL').click();
    const dialog = this.dialog('Add URL');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('textbox', { name: 'URL' }).fill(opts.url);
    if (opts.urlType) {
      await this.selectOption(dialog.getByRole('combobox', { name: /^URL Type/ }), URL_TYPE_LABEL[opts.urlType]);
    }
    if (opts.enabled === false) {
      await this.selectOption(dialog.getByRole('combobox', { name: /^Status/ }), 'Disabled');
    }
    if (opts.bareIds) {
      await dialog.getByRole('checkbox', { name: 'Harvest bare content IDs' }).check();
    }
    await dialog.getByRole('button', { name: 'Add', exact: true }).click();
    await expect(dialog).toBeHidden();
  }

  async scrape(url: string): Promise<void> {
    await this.row(url).getByRole('button', { name: `Scrape URL ${url}` }).click();
  }

  async edit(url: string): Promise<Locator> {
    await this.rowMenuAction(this.row(url), url, 'Edit');
    const dialog = this.dialog('Edit URL');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async delete(url: string): Promise<void> {
    await this.rowMenuAction(this.row(url), url, 'Delete');
    await this.confirmDialog('Delete this source?', 'Delete');
  }

  async refresh(): Promise<void> {
    await this.headerButton('Refresh').click();
  }

  async scrapeAllEnabled(): Promise<void> {
    await this.headerButton('Scrape all').click();
    await this.confirmDialog('Scrape all enabled sources?', 'Scrape all');
  }

  enabledSwitch(url: string): Locator {
    return this.row(url).getByRole('checkbox', { name: `Enable ${url}` });
  }

  async toggleBareIds(url: string): Promise<void> {
    await this.rowMenuAction(this.row(url), url, 'Harvest bare IDs');
  }
}

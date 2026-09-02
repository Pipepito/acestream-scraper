import { expect, type Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export interface AddUrlOptions {
  url: string;
  urlType?: 'auto' | 'regular' | 'zeronet';
  enabled?: boolean;
  bareIds?: boolean;
}

const URL_TYPE_LABEL = { auto: 'Auto-detect', regular: 'Regular HTTP', zeronet: 'ZeroNet' } as const;

export class ScraperPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/scraper');
    await this.expectHeading('URL Scraper');
  }

  urlsRegion(): Locator {
    return this.region('Configured URLs');
  }

  row(url: string): Locator {
    return this.urlsRegion().getByRole('row').filter({ hasText: url });
  }

  async addUrl(opts: AddUrlOptions): Promise<void> {
    await this.page.getByRole('button', { name: 'Add URL' }).click();
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
    await this.row(url).getByRole('button', { name: `Edit URL ${url}` }).click();
    const dialog = this.dialog('Edit URL');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async delete(url: string): Promise<void> {
    this.acceptNextDialog();
    await this.row(url).getByRole('button', { name: `Delete URL ${url}` }).click();
  }

  async refresh(): Promise<void> {
    await this.page.getByRole('button', { name: 'Refresh', exact: true }).click();
  }

  async scrapeAllEnabled(): Promise<void> {
    this.acceptNextDialog();
    await this.page.getByRole('button', { name: 'Scrape All Enabled' }).click();
  }

  bareIdsSwitch(url: string): Locator {
    return this.row(url).getByRole('checkbox', { name: `Harvest bare content IDs for ${url}` });
  }
}

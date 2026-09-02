import type { Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class SettingsPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/settings');
    await this.expectHeading('Settings');
  }

  engineRegion(): Locator {
    return this.region('Engine connection');
  }

  async refreshEngineStatus(): Promise<void> {
    await this.engineRegion().getByRole('button', { name: 'Refresh status' }).click();
  }

  async saveEngineUrl(url: string): Promise<void> {
    const region = this.region('Connection settings');
    await region.getByRole('textbox', { name: 'Acestream Engine URL' }).fill(url);
    await region.getByRole('button', { name: 'Save engine URL' }).click();
  }

  async saveBaseUrl(url: string): Promise<void> {
    const region = this.region('Connection settings');
    await region.getByRole('textbox', { name: 'Base URL' }).fill(url);
    await region.getByRole('button', { name: 'Save base URL' }).click();
  }

  themeRadio(mode: 'Light theme' | 'Dark theme'): Locator {
    return this.page.getByRole('radio', { name: mode });
  }

  baseUrlsRegion(): Locator {
    return this.region('Stream base URLs');
  }

  async addBaseUrl(name: string, pattern: string, isDefault = false): Promise<void> {
    const region = this.baseUrlsRegion();
    await region.getByRole('textbox', { name: 'Name' }).fill(name);
    await region.getByRole('textbox', { name: 'Pattern' }).fill(pattern);
    if (isDefault) await region.getByRole('checkbox', { name: 'Set as default' }).check();
    await region.getByRole('button', { name: 'Add base URL' }).click();
  }

  async deleteBaseUrl(name: string): Promise<void> {
    await this.baseUrlsRegion().getByRole('button', { name: `Delete base URL ${name}` }).click();
  }

  inventoryRow(key: string): Locator {
    return this.page.getByTestId(`settings-inventory-row-${key}`);
  }

  async saveRescrapeInterval(hours: string): Promise<void> {
    const region = this.region('Automation settings');
    await region.getByRole('spinbutton', { name: 'Rescrape Interval (hours)' }).fill(hours);
    await region.getByRole('button', { name: 'Save rescrape interval' }).click();
  }

  addPidSwitch(): Locator {
    return this.page.getByRole('checkbox', { name: 'Append PID to generated Acestream links' });
  }
}

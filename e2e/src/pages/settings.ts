import { expect, type Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class SettingsPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/settings');
    await this.expectHeading('Settings');
  }

  engine(): Locator {
    return this.region('Engine');
  }

  engineStatus(): Locator {
    return this.statusLine('Engine status');
  }

  async refreshEngineStatus(): Promise<void> {
    await this.engine().getByRole('button', { name: 'Refresh status' }).click();
  }

  async saveEngineUrl(url: string): Promise<void> {
    await this.engine().getByRole('textbox', { name: 'Acestream Engine URL' }).fill(url);
    await this.engine().getByRole('button', { name: 'Save engine URL' }).click();
  }

  linkFormats(): Locator {
    return this.region('Stream link formats');
  }

  async addLinkFormat(name: string, pattern: string, isDefault = false): Promise<void> {
    await this.linkFormats().getByRole('button', { name: 'Add format' }).click();
    const dialog = this.dialog('Add link format');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('textbox', { name: 'Name' }).fill(name);
    await dialog.getByRole('textbox', { name: 'Pattern' }).fill(pattern);
    if (isDefault) await dialog.getByRole('checkbox', { name: 'Set as default' }).check();
    await dialog.getByRole('button', { name: 'Add base URL' }).click();
    await expect(dialog).toBeHidden();
  }

  async deleteLinkFormat(name: string): Promise<void> {
    await this.linkFormats().getByRole('button', { name: `Delete base URL ${name}` }).click();
    await this.confirmDialog(new RegExp(`^Delete the link format “${name}”\\?$`), 'Delete');
  }

  automation(): Locator {
    return this.region('Automation');
  }

  async saveInterval(label: 'Scrape sources every (hours)' | 'Refresh EPG every (hours)', hours: string): Promise<void> {
    const form = this.automation().getByRole('form', { name: `${label} form` });
    await form.getByRole('spinbutton', { name: label }).fill(hours);
    await form.getByRole('button', { name: 'Save' }).click();
  }

  addPidSwitch(): Locator {
    return this.page.getByRole('checkbox', { name: 'Append PID to stream links' });
  }

  appIdSwitch(): Locator {
    return this.page.getByRole('checkbox', { name: 'Use AppID in stream links' });
  }
}

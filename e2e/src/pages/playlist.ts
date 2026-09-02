import type { Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class PlaylistPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/playlist');
    await this.expectHeading('Playlist');
  }

  downloadLink(): Locator {
    return this.page.getByRole('link', { name: 'Download M3U' });
  }

  playlistUrlField(): Locator {
    return this.page.locator('input[value*="/playlists/m3u"]');
  }

  onlyOnline(): Locator {
    return this.page.getByRole('checkbox', { name: 'Only include online channels' });
  }

  favoritesOnly(): Locator {
    return this.page.getByRole('checkbox', { name: 'Only include favorite TV channels' });
  }

  searchField(): Locator {
    return this.page.getByRole('textbox', { name: 'Search Channels' });
  }

  async selectBaseUrl(option: string | RegExp): Promise<void> {
    await this.selectOption(this.page.getByRole('combobox', { name: /^Stream base URL/ }), option);
  }

  async showAdvanced(): Promise<void> {
    await this.page.getByRole('button', { name: 'Show advanced options' }).click();
  }

  qrButton(): Locator {
    return this.page.getByRole('button', { name: 'Show QR Code' });
  }
}

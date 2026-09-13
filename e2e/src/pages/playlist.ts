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
    return this.page.getByRole('textbox', { name: 'Playlist URL' });
  }

  copyButton(): Locator {
    return this.page.getByRole('button', { name: 'Copy playlist URL' });
  }

  onlyOnline(): Locator {
    return this.page.getByRole('checkbox', { name: 'Only online channels' });
  }

  favoritesOnly(): Locator {
    return this.page.getByRole('checkbox', { name: 'Favorite TV channels only' });
  }

  searchField(): Locator {
    return this.page.getByRole('textbox', { name: 'Search channels' });
  }

  async selectBaseUrl(option: string | RegExp): Promise<void> {
    await this.selectOption(this.page.getByRole('combobox', { name: /^Stream link format/ }), option);
  }

  async showGroupFilters(): Promise<void> {
    await this.page.getByRole('button', { name: 'Group filters' }).click();
  }

  qrButton(): Locator {
    return this.page.getByRole('button', { name: 'Show QR code' });
  }
}

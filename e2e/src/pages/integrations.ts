import { expect, type Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export interface RemotePlayerFields {
  name: string;
  kind: 'VLC (desktop)' | 'Kodi';
  host: string;
  port: number;
  password?: string;
}

/** The Integrations page: public address, web player, remote players and media servers. */
export class IntegrationsPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/integrations');
    await this.expectHeading('Integrations');
  }

  summary(): Locator {
    return this.statusLine('Integration summary');
  }

  /** Exact match: an empty section renders its own nested region ("No media servers yet"). */
  private section(title: string): Locator {
    return this.page.getByRole('region', { name: title, exact: true });
  }

  publicAddressSection(): Locator {
    return this.section('Public address');
  }

  webPlayerSection(): Locator {
    return this.section('Web player');
  }

  remotePlayersSection(): Locator {
    return this.section('Remote players');
  }

  mediaServersSection(): Locator {
    return this.section('Media servers');
  }

  playerCard(name: string): Locator {
    return this.page.getByRole('group', { name: `Player ${name}` });
  }

  serverCard(name: string): Locator {
    return this.page.getByRole('group', { name: `Media server ${name}` });
  }

  /** Open "Add player" and fill the dialog, without submitting. */
  async openAddPlayer(fields: RemotePlayerFields): Promise<Locator> {
    await this.remotePlayersSection().getByRole('button', { name: 'Add player', exact: true }).click();
    const dialog = this.dialog('Add player');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('textbox', { name: 'Name', exact: true }).fill(fields.name);
    await this.selectOption(dialog.getByRole('combobox', { name: 'Player' }), fields.kind);
    await dialog.getByRole('textbox', { name: 'Host', exact: true }).fill(fields.host);
    await dialog.getByRole('textbox', { name: 'Port', exact: true }).fill(String(fields.port));
    if (fields.password !== undefined) await dialog.getByLabel('Password', { exact: true }).fill(fields.password);
    return dialog;
  }

  /** Submit the open Add player dialog; resolves once the player's card is on the page. */
  async savePlayer(name: string): Promise<void> {
    const dialog = this.dialog('Add player');
    await dialog.getByRole('button', { name: 'Add player', exact: true }).click();
    await expect(dialog).toBeHidden();
    await expect(this.playerCard(name)).toBeVisible();
  }

  /** Fill the dialog and save it in one go, for a player whose probe does not matter. */
  async addPlayer(fields: RemotePlayerFields): Promise<void> {
    await this.openAddPlayer(fields);
    await this.savePlayer(fields.name);
  }

  /** Run the dialog's inline probe. The dialog must already be open. */
  async testConnection(): Promise<void> {
    const dialog = this.page.getByRole('dialog');
    await dialog.getByRole('button', { name: 'Test connection' }).click();
  }

  /** The probe result the dialog shows, as guided plain-language copy. */
  async expectProbe(text: string | RegExp): Promise<void> {
    await expect(this.page.getByRole('dialog').getByRole('alert').filter({ hasText: text }).first()).toBeVisible({ timeout: 30_000 });
  }

  async deletePlayer(name: string): Promise<void> {
    await this.rowMenuAction(this.playerCard(name), name, 'Delete');
    await this.confirmDialog(`Delete ${name}?`, 'Delete');
    await expect(this.playerCard(name)).toHaveCount(0);
  }
}

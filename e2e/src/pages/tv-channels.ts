import { expect, type Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export interface TvChannelForm {
  name: string;
  description?: string;
  category?: string;
  country?: string;
  language?: string;
  logoUrl?: string;
  favorite?: boolean;
  active?: boolean;
}

export class TVChannelsPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/tv-channels');
    await this.expectHeading('TV Channels');
  }

  inventory(): Locator {
    return this.page.getByRole('region', { name: 'TV channel inventory' });
  }

  row(name: string): Locator {
    return this.inventory().getByRole('row').filter({ hasText: name });
  }

  async add(form: TvChannelForm): Promise<void> {
    await this.page.getByRole('button', { name: 'Add TV Channel' }).click();
    const dialog = this.dialog('Add TV Channel');
    await expect(dialog).toBeVisible();
    await this.fillForm(dialog, form);
    await dialog.getByRole('button', { name: 'Create' }).click();
    await expect(dialog).toBeHidden();
  }

  async fillForm(dialog: Locator, form: Partial<TvChannelForm>): Promise<void> {
    if (form.name !== undefined) await dialog.getByRole('textbox', { name: 'Channel Name' }).fill(form.name);
    if (form.description !== undefined) await dialog.getByRole('textbox', { name: 'Description' }).fill(form.description);
    if (form.logoUrl !== undefined) await dialog.getByRole('textbox', { name: 'Logo URL' }).fill(form.logoUrl);
    if (form.category !== undefined) await dialog.getByRole('textbox', { name: 'Category' }).fill(form.category);
    if (form.country !== undefined) await dialog.getByRole('textbox', { name: 'Country' }).fill(form.country);
    if (form.language !== undefined) await dialog.getByRole('textbox', { name: 'Language' }).fill(form.language);
    if (form.favorite !== undefined) await dialog.getByRole('checkbox', { name: 'Favorite' }).setChecked(form.favorite);
    if (form.active !== undefined) await dialog.getByRole('checkbox', { name: 'Active' }).setChecked(form.active);
  }

  async openEdit(name: string): Promise<Locator> {
    await this.row(name).getByRole('button', { name: `edit tv channel ${name}` }).click();
    const dialog = this.dialog('Edit TV Channel');
    await expect(dialog).toBeVisible();
    return dialog;
  }

  async delete(name: string): Promise<void> {
    await this.row(name).getByRole('button', { name: `delete tv channel ${name}` }).click();
    const dialog = this.dialog('Delete TV Channel');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('button', { name: 'Delete TV Channel' }).click();
    await expect(dialog).toBeHidden();
  }

  favoriteToggle(name: string): Locator {
    return this.row(name).getByRole('button', { name: `toggle favorite for tv channel ${name}` });
  }

  playButton(name: string): Locator {
    return this.row(name).getByRole('button', { name: `play tv channel ${name}` });
  }

  async refresh(): Promise<void> {
    await this.page.getByTestId('page-header-actions').getByRole('button', { name: 'Refresh', exact: true }).click();
  }

  favoritesOnly(): Locator {
    return this.page.getByRole('checkbox', { name: 'Favorites only' });
  }
}

export class TVChannelDetailPage extends AppShell {
  async open(id: number, name: string | RegExp): Promise<void> {
    await this.goto(`/tv-channels/${id}`);
    await this.expectHeading(name);
  }

  coverage(): Locator {
    return this.region('Acestream Coverage');
  }

  streamItem(name: string): Locator {
    return this.coverage().getByRole('group', { name: `Acestream actions for ${name}` }).locator('xpath=ancestor::li[1]');
  }

  async addSingle(search: string, names: string[]): Promise<void> {
    await this.coverage().getByRole('button', { name: 'Add Single' }).click();
    const dialog = this.dialog('Associate Acestream Channel');
    await expect(dialog).toBeVisible();
    await dialog.getByRole('textbox', { name: 'Search by name, group, or ID' }).fill(search);
    for (const name of names) {
      await dialog.getByRole('checkbox', { name: `Select acestream ${name}` }).check();
    }
    await dialog.getByRole('button', { name: 'Assign Selected' }).click();
    await expect(dialog).toBeHidden();
  }

  async batchAdd(ids: string[]): Promise<Locator> {
    await this.coverage().getByRole('button', { name: 'Batch Add' }).click();
    const dialog = this.dialog(/Batch Associate Acestreams to/);
    await expect(dialog).toBeVisible();
    await dialog.getByRole('textbox', { name: 'Acestream IDs' }).fill(ids.join('\n'));
    await dialog.getByRole('button', { name: 'Associate' }).click();
    return dialog;
  }

  async removeStream(name: string): Promise<void> {
    this.acceptNextDialog();
    await this.coverage().getByRole('button', { name: `Remove acestream ${name}` }).click();
  }

  epgSchedule(): Locator {
    return this.region('EPG Schedule');
  }

  async startEdit(): Promise<void> {
    await this.page.getByTestId('page-header-actions').getByRole('button', { name: 'Edit', exact: true }).click();
  }

  async save(): Promise<void> {
    await this.page.getByTestId('page-header-actions').getByRole('button', { name: 'Save', exact: true }).click();
  }
}

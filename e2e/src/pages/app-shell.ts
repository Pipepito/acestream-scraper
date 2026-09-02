import { expect, type Locator, type Page } from '@playwright/test';

export type NavLabel =
  | 'Dashboard'
  | 'Scraper'
  | 'Acestream Search'
  | 'Acestream Channels'
  | 'EPG Sources'
  | 'EPG Mappings'
  | 'TV Channels'
  | 'Playlist'
  | 'WARP Status'
  | 'Settings'
  | 'Health'
  | 'Stats';

export const NAV_ROUTES: Record<NavLabel, string> = {
  Dashboard: '/',
  Scraper: '/scraper',
  'Acestream Search': '/search',
  'Acestream Channels': '/acestream-channels',
  'EPG Sources': '/epg',
  'EPG Mappings': '/epg/mappings',
  'TV Channels': '/tv-channels',
  Playlist: '/playlist',
  'WARP Status': '/warp',
  Settings: '/settings',
  Health: '/health',
  Stats: '/stats',
};

/** Shell-level interactions shared by every page: navigation, regions, dialogs, MUI widgets. */
export class AppShell {
  constructor(readonly page: Page) {}

  async goto(path: string): Promise<void> {
    await this.page.goto(path);
    await this.page.waitForLoadState('domcontentloaded');
  }

  nav(): Locator {
    return this.page.getByRole('navigation', { name: 'navigation menu' });
  }

  async navigate(label: NavLabel): Promise<void> {
    await this.nav().getByRole('link', { name: label, exact: true }).click();
  }

  heading(): Locator {
    return this.page.getByRole('heading', { level: 1 }).first();
  }

  async expectHeading(name: string | RegExp): Promise<void> {
    await expect(this.heading()).toHaveText(name);
  }

  region(name: string | RegExp): Locator {
    return this.page.getByRole('region', { name });
  }

  dialog(name: string | RegExp): Locator {
    return this.page.getByRole('dialog', { name });
  }

  /** MUI Snackbar/Alert containing `text`. */
  alert(text: string | RegExp): Locator {
    return this.page.getByRole('alert').filter({ hasText: text });
  }

  async expectAlert(text: string | RegExp, timeout = 15_000): Promise<void> {
    await expect(this.alert(text).first()).toBeVisible({ timeout });
  }

  themeToggle(): Locator {
    return this.page.getByRole('button', { name: /Switch to (dark|light) theme/ });
  }

  /** Auto-accept the next window.confirm(); call right before the click that triggers it. */
  acceptNextDialog(): void {
    this.page.once('dialog', (d) => void d.accept());
  }

  dismissNextDialog(): void {
    this.page.once('dialog', (d) => void d.dismiss());
  }

  /** Open a MUI (non-native) Select and pick an option by its visible text. */
  async selectOption(combobox: Locator, option: string | RegExp): Promise<void> {
    await combobox.click();
    const listbox = this.page.getByRole('listbox');
    await expect(listbox).toBeVisible();
    await listbox.getByRole('option', { name: option }).click();
    await expect(listbox).toBeHidden();
  }

  /** MUI Select whose accessible name is only its value (no labelId): scope by the FormControl label text. */
  comboboxByFormLabel(label: string): Locator {
    return this.page.locator('.MuiFormControl-root', { hasText: label }).getByRole('combobox').first();
  }
}

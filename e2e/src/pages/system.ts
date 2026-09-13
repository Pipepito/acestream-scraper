import type { Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class OverviewPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/');
    await this.expectHeading('Overview');
  }
  statusChip(): Locator {
    return this.page.getByTestId('page-header-actions').getByText(/^(HEALTHY|ATTENTION)$/);
  }
  summary(): Locator {
    return this.statusLine('Overview summary');
  }
  async refresh(): Promise<void> {
    await this.page.getByRole('button', { name: 'Refresh', exact: true }).first().click();
  }
  services(): Locator {
    return this.region('Services');
  }
  serviceCard(label: string): Locator {
    return this.services().getByRole('group', { name: `Service ${label}` });
  }
  restartButton(label: string): Locator {
    return this.serviceCard(label).getByRole('button', { name: `Restart ${label}` });
  }
  async restart(label: string): Promise<void> {
    await this.restartButton(label).click();
    await this.confirmDialog(`Restart ${label}?`, 'Restart service');
  }
  inventory(): Locator {
    return this.region('Inventory');
  }
  inventoryGroup(title: 'Streams' | 'TV channels' | 'Sources and guide'): Locator {
    return this.inventory().getByRole('region', { name: title });
  }
  scheduledJobs(): Locator {
    return this.region('Scheduled jobs').getByRole('table', { name: 'Scheduled jobs' });
  }
}

export class WarpPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/warp');
    await this.expectHeading('WARP');
  }
  status(): Locator {
    return this.statusLine('WARP status');
  }
  connectionDetails(): Locator {
    return this.region('Connection details');
  }
  modeAndLicense(): Locator {
    return this.region('Mode and license');
  }
}

import type { Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class SystemPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/system');
    await this.expectHeading('System status');
  }
  statusChip(): Locator {
    return this.page.getByTestId('page-header-actions').getByText(/^(Services healthy|Services need attention|Status unavailable)$/);
  }
  summary(): Locator {
    return this.statusLine('System status summary');
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

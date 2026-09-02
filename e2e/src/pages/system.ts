import type { Locator } from '@playwright/test';
import { AppShell } from './app-shell';

export class DashboardPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/');
    await this.expectHeading('Dashboard');
  }
  readiness(): Locator {
    return this.region('System readiness');
  }
  backgroundTasks(): Locator {
    return this.region('Background Tasks');
  }
  recentActivity(): Locator {
    return this.region('Recent Activity');
  }
  autoRefreshSwitch(): Locator {
    return this.page.getByRole('checkbox', { name: 'Auto-Refresh' });
  }
  retentionSelect(): Locator {
    return this.comboboxByFormLabel('Retention');
  }
}

export class HealthPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/health');
    await this.expectHeading('Health');
  }
  statusChip(): Locator {
    return this.page.getByTestId('page-header-actions').getByText(/^(HEALTHY|DEGRADED|ERROR)$/);
  }
  overview(): Locator {
    return this.region('Status overview');
  }
  totals(): Locator {
    return this.region('Supporting totals');
  }
  async refresh(): Promise<void> {
    await this.overview().getByRole('button', { name: 'Refresh status' }).click();
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
    const dialog = this.dialog(`Restart ${label}?`);
    await dialog.getByRole('button', { name: 'Restart service' }).click();
  }
}

export class StatsPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/stats');
    await this.expectHeading('Stats');
  }
  summary(): Locator {
    return this.page.getByTestId('stats-summary-metrics');
  }
  breakdown(): Locator {
    return this.page.getByTestId('stats-breakdown-groups');
  }
}

export class WarpPage extends AppShell {
  async open(): Promise<void> {
    await this.goto('/warp');
    await this.expectHeading('WARP');
  }
  connectionStatus(): Locator {
    return this.region('Connection status');
  }
  modeAndLicense(): Locator {
    return this.region('Mode and license');
  }
}

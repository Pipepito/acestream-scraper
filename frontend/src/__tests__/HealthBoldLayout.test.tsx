import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

import Health from '../pages/Health';
import { createAppTheme } from '../theme';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
import { TestMemoryRouter } from '../testUtils/router';
import * as configHooks from '../hooks/useConfig';

jest.mock('../hooks/useConfig');
jest.mock('../components/ServicesPanel', () => ({
  __esModule: true,
  default: () => <div data-testid="services-panel" />,
}));

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

const renderHealthPage = (theme = createAppTheme('light')) =>
  render(
    <ThemeProvider theme={theme}>
      <TestMemoryRouter>
        <Health />
      </TestMemoryRouter>
    </ThemeProvider>
  );

describe('Health bold layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseMediaQuery.mockReset();
    mockResponsiveShellQueries(mockUseMediaQuery, createAppTheme('light'), {
      isPhone: false,
      isDesktop: true,
      isWideDesktop: true,
    });

    (configHooks.useHealth as jest.Mock).mockReturnValue({
      data: {
        status: 'healthy',
        version: '1.0.0',
        acestream: { status: 'online', message: 'Engine reachable' },
        settings: { region: 'EU', profile: 'Default' },
      },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });
    (configHooks.useStats as jest.Mock).mockReturnValue({
      data: {
        channels: { total: 120, online: 112, offline: 4, unknown: 4 },
        urls: { total: 210, active: 202, error: 8 },
        epg: { sources: 7, channels: 95, programs: 5000 },
      },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });
  });

  it('leads with readiness and next-step guidance before the later operational sections', () => {
    renderHealthPage();

    const statusOverviewHeading = screen.getByRole('heading', { level: 2, name: 'Status overview' });
    const operationalDetailsHeading = screen.getByRole('heading', { level: 2, name: 'Operational details' });
    const supportingTotalsHeading = screen.getByRole('heading', { level: 2, name: 'Supporting totals' });
    const readinessSummary = screen.getByText('Healthy and ready for scraper, playlist, channel, and EPG work.');
    const nextStepLabel = screen.getByText('Next step');

    expect(statusOverviewHeading.compareDocumentPosition(readinessSummary) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(readinessSummary.compareDocumentPosition(nextStepLabel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(readinessSummary.compareDocumentPosition(operationalDetailsHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(nextStepLabel.compareDocumentPosition(supportingTotalsHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText('Continue with scraper, playlist, channel, or EPG work.')).toBeInTheDocument();
  });

  it('keeps runtime details, configuration snapshot, and supporting totals visible after the readiness summary', () => {
    renderHealthPage();

    expect(screen.getByRole('heading', { level: 3, name: 'Runtime details' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: 'Configuration snapshot' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Supporting totals' })).toBeInTheDocument();
  });

  it('keeps the readiness summary, next step, and refresh action visible on narrow widths', () => {
    const theme = createAppTheme('light');

    mockResponsiveShellQueries(mockUseMediaQuery, theme, {
      isPhone: true,
      isDesktop: false,
      isWideDesktop: false,
    });

    renderHealthPage(theme);

    const statusOverview = screen.getByRole('region', { name: 'Status overview' });

    expect(within(statusOverview).getByText('Healthy and ready for scraper, playlist, channel, and EPG work.')).toBeInTheDocument();
    expect(within(statusOverview).getByText('Next step')).toBeInTheDocument();
    expect(within(statusOverview).getByRole('button', { name: 'Refresh status' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 2, name: 'Operational details' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Supporting totals' })).toBeInTheDocument();
  });
});

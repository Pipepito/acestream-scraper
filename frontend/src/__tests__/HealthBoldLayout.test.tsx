import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';

import Health from '../pages/Health';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as configHooks from '../hooks/useConfig';

jest.mock('../hooks/useConfig');

describe('Health bold layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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

  it('renders a readiness-led health summary with next-step guidance', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Health />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByRole('heading', { level: 2, name: 'Status overview' })).toBeInTheDocument();
    expect(screen.getByText('System readiness')).toBeInTheDocument();
    expect(screen.getByText(/healthy and ready for scraper and channel work/i)).toBeInTheDocument();
    expect(screen.getByText(/^Next step$/i)).toBeInTheDocument();
    expect(screen.getByText(/continue with scraper, playlist, or channel tasks/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'System totals' })).toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';

import WarpPage from '../pages/WARP';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as warpHooks from '../hooks/useWarp';
import { WarpMode } from '../types/warpTypes';

jest.mock('../hooks/useWarp');

describe('WARP bold layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (warpHooks.useWarpStatus as jest.Mock).mockReturnValue({
      data: {
        running: true,
        connected: true,
        mode: WarpMode.WARP,
        account_type: 'free',
        ip: '203.0.113.1',
        location: 'GB',
        colo: 'LHR',
        tunnel: { protocol: 'MASQUE (HTTPS via UDP)', latency: '11ms', loss: '0.00%', last_handshake: '658s', sent: '2.8MB', received: '14.2MB', endpoints: '162.159.198.2', colo: 'LHR', tls_version: 'TLSv1.3' },
        registration: { device_id: 'dev-1234', account_id: 'acc-5678', license: 'Tz4K…K92k' },
        cf_trace: { colo: 'LHR' },
      },
      isLoading: false,
      error: undefined,
    });
    (warpHooks.useWarpConnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
    (warpHooks.useWarpDisconnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
    (warpHooks.useWarpSetMode as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    (warpHooks.useWarpRegisterLicense as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
  });

  it('renders a connection-readiness hero with next-step guidance', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <WarpPage />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByText('Tunnel pulse')).toBeInTheDocument();
    expect(screen.getByText(/warp is connected and ready to protect scraper traffic/i)).toBeInTheDocument();
    expect(screen.getByText(/^Protection state$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Next step$/i)).toBeInTheDocument();
    expect(screen.getByText(/keep the current tunnel active or change mode before you run more network-sensitive tasks/i)).toBeInTheDocument();
  });

  it('shows the public IP, exit location, tunnel and registration details when connected', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <WarpPage />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    const path = screen.getByRole('region', { name: 'Current path' });
    expect(within(path).getByText('IP: 203.0.113.1')).toBeInTheDocument();
    expect(within(path).getByText('Exit location: GB via LHR')).toBeInTheDocument();

    const tunnel = screen.getByRole('region', { name: 'Tunnel details' });
    expect(within(tunnel).getByText('Protocol: MASQUE (HTTPS via UDP)')).toBeInTheDocument();
    expect(within(tunnel).getByText('Latency: 11ms')).toBeInTheDocument();
    expect(within(tunnel).getByText('Packet loss: 0.00%')).toBeInTheDocument();
    expect(within(tunnel).getByText('Traffic: 2.8MB sent, 14.2MB received')).toBeInTheDocument();

    const registration = screen.getByRole('region', { name: 'Registration' });
    expect(within(registration).getByText('Device ID: dev-1234')).toBeInTheDocument();
    expect(within(registration).getByText('License: Tz4K…K92k')).toBeInTheDocument();
  });
});

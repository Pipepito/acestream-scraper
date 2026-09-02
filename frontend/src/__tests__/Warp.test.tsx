import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import WarpPage, { describeWarpStatus } from '../pages/WARP';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as warpHooks from '../hooks/useWarp';
import { WarpMode } from '../types/warpTypes';

jest.mock('../hooks/useWarp');

const connectedStatus = {
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
};

describe('WARP page', () => {
  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <WarpPage />
        </TestMemoryRouter>
      </ThemeProvider>
    );

  beforeEach(() => {
    jest.clearAllMocks();
    (warpHooks.useWarpStatus as jest.Mock).mockReturnValue({ data: connectedStatus, isLoading: false, error: undefined });
    (warpHooks.useWarpConnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
    (warpHooks.useWarpDisconnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
    (warpHooks.useWarpSetMode as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    (warpHooks.useWarpRegisterLicense as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
  });

  it('describes the tunnel in one sentence', () => {
    expect(describeWarpStatus(connectedStatus)).toBe('Connected · mode warp · free account · exit GB via LHR');
    expect(describeWarpStatus({ ...connectedStatus, connected: false })).toBe('Disconnected · mode warp · free account');
    expect(describeWarpStatus({ ...connectedStatus, running: false })).toBe('Not running');
    expect(describeWarpStatus(undefined)).toBe('Not running');
  });

  it('shows one status row, the details cards and the mode form when connected', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'WARP' })).toBeInTheDocument();
    const status = screen.getByRole('status', { name: 'WARP status' });
    expect(status).toHaveTextContent('Connected');
    expect(status).toHaveTextContent('Connected · mode warp · free account · exit GB via LHR');
    expect(screen.queryByText('Tunnel pulse')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to Overview' })).toHaveAttribute('href', '/');
    expect(screen.getByRole('button', { name: 'Connect' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Disconnect' })).toBeEnabled();

    const path = screen.getByRole('region', { name: 'Current path' });
    expect(within(path).getByText('IP: 203.0.113.1')).toBeInTheDocument();
    expect(within(path).getByText('Exit location: GB via LHR')).toBeInTheDocument();
    expect(within(path).queryByText(/Mode:/)).not.toBeInTheDocument();

    const tunnel = screen.getByRole('region', { name: 'Tunnel details' });
    expect(within(tunnel).getByText('Protocol: MASQUE (HTTPS via UDP)')).toBeInTheDocument();
    expect(within(tunnel).getByText('Latency: 11ms')).toBeInTheDocument();
    expect(within(tunnel).getByText('Traffic: 2.8MB sent, 14.2MB received')).toBeInTheDocument();

    const registration = screen.getByRole('region', { name: 'Registration' });
    expect(within(registration).getByText('Device ID: dev-1234')).toBeInTheDocument();
    expect(within(registration).getByText('License: Tz4K…K92k')).toBeInTheDocument();

    expect(screen.getByRole('heading', { level: 2, name: 'Mode and license' })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Mode' })).toHaveTextContent(/warp/i);
    expect(screen.getByRole('button', { name: 'Set Mode' })).toBeDisabled();
  });

  it('explains how to enable WARP when it is not running and hides the mode form', () => {
    (warpHooks.useWarpStatus as jest.Mock).mockReturnValue({
      data: { running: false, connected: false, mode: null, account_type: '', ip: null, cf_trace: {} },
      isLoading: false,
      error: undefined,
    });
    renderPage();

    expect(screen.getByRole('status', { name: 'WARP status' })).toHaveTextContent('Not running');
    expect(screen.getByText(/WARP is not running in this container/)).toBeInTheDocument();
    expect(screen.getByText('ENABLE_WARP=true')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { level: 2, name: 'Mode and license' })).not.toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Current path' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Connect' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Disconnect' })).toBeDisabled();
  });
});

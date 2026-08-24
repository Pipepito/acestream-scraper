import React from 'react';
import { render, screen } from '@testing-library/react';
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
});

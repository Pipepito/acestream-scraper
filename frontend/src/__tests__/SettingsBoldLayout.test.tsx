import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';

import Settings from '../pages/Settings';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as configHooks from '../hooks/useConfig';
import { configService } from '../services/configService';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';

jest.mock('../bootstrap/AppBootstrap', () => {
  const actual = jest.requireActual('../bootstrap/AppBootstrap');
  return { ...actual, useAppThemeMode: jest.fn() };
});

jest.mock('../hooks/useConfig');
jest.mock('../services/configService', () => ({
  configService: {
    getAppId: jest.fn(),
    updateAppId: jest.fn(),
  },
}));

describe('Settings bold layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAppThemeMode as jest.Mock).mockReturnValue({
      mode: 'light',
      setMode: jest.fn(),
      toggleMode: jest.fn(),
    });
    (configHooks.useBaseUrl as jest.Mock).mockReturnValue({ data: 'acestream://', isLoading: false });
    (configHooks.useUpdateBaseUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
    (configHooks.useAceEngineUrl as jest.Mock).mockReturnValue({ data: 'http://localhost:6878', isLoading: false });
    (configHooks.useUpdateAceEngineUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
    (configHooks.useRescrapeInterval as jest.Mock).mockReturnValue({ data: 24, isLoading: false });
    (configHooks.useUpdateRescrapeInterval as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
    (configHooks.useAddPid as jest.Mock).mockReturnValue({ data: true, isLoading: false });
    (configHooks.useUpdateAddPid as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
    (configHooks.useAcestreamStatus as jest.Mock).mockReturnValue({
      data: { status: 'online', message: 'Engine online and ready' },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });
    (configService.getAppId as jest.Mock).mockResolvedValue(true);
    (configService.updateAppId as jest.Mock).mockResolvedValue(undefined);
  });

  it('renders a settings summary hero that frames connection status and next actions', async () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Settings />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(await screen.findByText('Control center')).toBeInTheDocument();
    expect(screen.getByText(/settings are ready for connection checks and automation tuning/i)).toBeInTheDocument();
    expect(screen.getByText(/^Priority check$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Next step$/i)).toBeInTheDocument();
    expect(screen.getByText(/confirm the engine is reachable, then update urls or automation only if your environment changed/i)).toBeInTheDocument();
  });
});

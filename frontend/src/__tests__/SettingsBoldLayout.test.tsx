import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';

import Settings from '../pages/Settings';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as configHooks from '../hooks/useConfig';
import * as baseUrlHooks from '../hooks/useBaseUrls';
import { ApiError } from '../services/apiErrors';
import { configService } from '../services/configService';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';

jest.mock('../bootstrap/AppBootstrap', () => {
  const actual = jest.requireActual('../bootstrap/AppBootstrap');
  return { ...actual, useAppThemeMode: jest.fn() };
});

jest.mock('../hooks/useConfig');
jest.mock('../hooks/useBaseUrls');
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
    (configHooks.useAllSettings as jest.Mock).mockReturnValue({
      data: {
        base_url: 'acestream://',
        ace_engine_url: 'http://localhost:6878',
        rescrape_interval: '24',
        addpid: 'true',
        appid: 'true',
        playlist_name: 'Daily Channels',
        xmltv_url: 'https://example.test/epg.xml',
      },
      isLoading: false,
      error: undefined,
    });
    (configHooks.useAcestreamStatus as jest.Mock).mockReturnValue({
      data: { status: 'online', message: 'Engine online and ready' },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });
    (configService.getAppId as jest.Mock).mockResolvedValue(true);
    (configService.updateAppId as jest.Mock).mockResolvedValue(undefined);
    (baseUrlHooks.useBaseUrls as jest.Mock).mockReturnValue({
      data: [
        { id: 1, name: 'Ace player', pattern: 'acestream://', is_default: true },
        {
          id: 2,
          name: 'Local HLS',
          pattern: 'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}',
          is_default: false,
        },
      ],
      isLoading: false,
      error: undefined,
    });
    (baseUrlHooks.useCreateBaseUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
    (baseUrlHooks.usePatchBaseUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
    (baseUrlHooks.useDeleteBaseUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
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

  it('keeps the settings inventory secondary to the existing editable workflow', async () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Settings />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    const heroCopy = await screen.findByText(/settings are ready for connection checks and automation tuning/i);
    const connectionHeading = screen.getByRole('heading', { level: 2, name: 'Connection settings' });
    const automationHeading = screen.getByRole('heading', { level: 2, name: 'Automation settings' });
    const inventoryHeading = screen.getByRole('heading', { level: 2, name: 'Settings inventory' });
    const commonGroupHeading = screen.getByRole('heading', { level: 3, name: 'Common connection settings' });
    const automationGroupHeading = screen.getByRole('heading', { level: 3, name: 'Automation settings' });
    const advancedGroupHeading = screen.getByRole('heading', { level: 3, name: 'Advanced/internal settings' });

    expect(heroCopy).toBeInTheDocument();
    expect(screen.getByText(/saved backend values appear here\./i)).toBeInTheDocument();
    expect(screen.getByText(/unsaved edits above do not appear here until save succeeds\./i)).toBeInTheDocument();
    expect(commonGroupHeading).toBeInTheDocument();
    expect(automationGroupHeading).toBeInTheDocument();
    expect(advancedGroupHeading).toBeInTheDocument();
    expect(connectionHeading.compareDocumentPosition(inventoryHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(automationHeading.compareDocumentPosition(inventoryHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('lists named stream base URLs with a default indicator and row actions', async () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Settings />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(await screen.findByRole('heading', { level: 2, name: 'Stream base URLs' })).toBeInTheDocument();
    expect(screen.getByText('Ace player')).toBeInTheDocument();
    expect(screen.getByText('Local HLS')).toBeInTheDocument();
    expect(screen.getByText('Default')).toBeInTheDocument();
    // The example in the helper text and the row pattern can render the same string.
    expect(screen.getAllByText('http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: 'Make default' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit base URL Local HLS' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete base URL Ace player' })).toBeInTheDocument();
  });

  it('promotes a non-default entry when its make-default action is used', async () => {
    const patchMutate = jest.fn();
    (baseUrlHooks.usePatchBaseUrl as jest.Mock).mockReturnValue({ mutate: patchMutate, isLoading: false });

    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Settings />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    fireEvent.click(await screen.findByRole('button', { name: 'Make default' }));

    expect(patchMutate).toHaveBeenCalledWith(
      { id: 2, data: { is_default: true } },
      expect.any(Object)
    );
  });

  it('shows a clear duplicate-name message when adding a base URL returns 409', async () => {
    const createMutate = jest.fn((_variables, options?: { onError?: (error: unknown) => void }) => {
      options?.onError?.(
        new ApiError({
          message: 'Conflict',
          status: 409,
          kind: 'unknown',
          canRetry: false,
        })
      );
    });
    (baseUrlHooks.useCreateBaseUrl as jest.Mock).mockReturnValue({ mutate: createMutate, isLoading: false });

    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Settings />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    await screen.findByRole('heading', { level: 2, name: 'Stream base URLs' });

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Ace player' } });
    fireEvent.change(screen.getByLabelText('Pattern'), { target: { value: 'acestream://' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add base URL' }));

    expect(createMutate).toHaveBeenCalledWith(
      { name: 'Ace player', pattern: 'acestream://', is_default: false },
      expect.any(Object)
    );
    expect(
      await screen.findByText('A base URL named "Ace player" already exists. Choose a different name.')
    ).toBeInTheDocument();
  });
});

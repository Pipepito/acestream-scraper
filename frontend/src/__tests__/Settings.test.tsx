import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Settings from '../pages/Settings';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as configHooks from '../hooks/useConfig';
import * as baseUrlHooks from '../hooks/useBaseUrls';
import { ApiError } from '../services/apiErrors';
import { configService } from '../services/configService';

jest.mock('../hooks/useConfig');
jest.mock('../hooks/useBaseUrls');
jest.mock('../services/configService', () => ({
  configService: { getAppId: jest.fn(), updateAppId: jest.fn() },
}));

type MutateOptions = { onSuccess?: () => void; onError?: (error: unknown) => void };
const succeedingMutate = () => jest.fn((_value: unknown, options?: MutateOptions) => options?.onSuccess?.());

describe('Settings page', () => {
  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Settings />
        </TestMemoryRouter>
      </ThemeProvider>
    );

  beforeEach(() => {
    jest.clearAllMocks();
    (configHooks.useBaseUrl as jest.Mock).mockReturnValue({ data: 'acestream://', isLoading: false });
    (configHooks.useUpdateBaseUrl as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
    (configHooks.useAceEngineUrl as jest.Mock).mockReturnValue({ data: 'http://localhost:6878', isLoading: false });
    (configHooks.useUpdateAceEngineUrl as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
    (configHooks.useRescrapeInterval as jest.Mock).mockReturnValue({ data: 24, isLoading: false });
    (configHooks.useUpdateRescrapeInterval as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
    (configHooks.useEpgRefreshInterval as jest.Mock).mockReturnValue({ data: 1, isLoading: false });
    (configHooks.useUpdateEpgRefreshInterval as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
    (configHooks.useAddPid as jest.Mock).mockReturnValue({ data: true, isLoading: false });
    (configHooks.useUpdateAddPid as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
    (configHooks.useAcestreamStatus as jest.Mock).mockReturnValue({
      data: { status: 'online', message: 'Engine online and ready' },
      isLoading: false,
      isFetching: false,
      error: undefined,
      refetch: jest.fn(),
    });
    (configService.getAppId as jest.Mock).mockResolvedValue(true);
    (configService.updateAppId as jest.Mock).mockResolvedValue(undefined);
    (baseUrlHooks.useBaseUrls as jest.Mock).mockReturnValue({
      data: [
        { id: 1, name: 'Ace player', pattern: 'acestream://', is_default: true },
        { id: 2, name: 'Local HLS', pattern: 'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}', is_default: false },
      ],
      isLoading: false,
      error: undefined,
    });
    (baseUrlHooks.useCreateBaseUrl as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
    (baseUrlHooks.usePatchBaseUrl as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
    (baseUrlHooks.useDeleteBaseUrl as jest.Mock).mockReturnValue({ mutate: succeedingMutate(), isPending: false });
  });

  it('shows one section per concern and drops the hero, appearance and inventory', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument();
    const headings = screen.getAllByRole('heading', { level: 2 }).map((heading) => heading.textContent);
    expect(headings).toEqual(['Engine', 'Stream link formats', 'Automation', 'API access']);
    expect(screen.queryByText('Control center')).not.toBeInTheDocument();
    expect(screen.queryByRole('radio', { name: 'Light theme' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Base URL')).not.toBeInTheDocument();

    const engineStatus = screen.getByRole('status', { name: 'Engine status' });
    expect(engineStatus).toHaveTextContent('Online');
    expect(engineStatus).toHaveTextContent('Engine online and ready');
    expect(screen.getByText('Adds the app id to acestream:// links for players that require it (rare).')).toBeInTheDocument();
  });

  it('saves both automation intervals and confirms with a snackbar', async () => {
    const rescrapeMutate = succeedingMutate();
    const epgMutate = succeedingMutate();
    (configHooks.useUpdateRescrapeInterval as jest.Mock).mockReturnValue({ mutate: rescrapeMutate, isPending: false });
    (configHooks.useUpdateEpgRefreshInterval as jest.Mock).mockReturnValue({ mutate: epgMutate, isPending: false });
    renderPage();

    const rescrape = await screen.findByLabelText('Scrape sources every (hours)');
    expect(rescrape).toHaveValue(24);
    const rescrapeSave = within(screen.getByRole('form', { name: 'Scrape sources every (hours) form' })).getByRole('button', { name: 'Save' });
    expect(rescrapeSave).toBeDisabled();
    fireEvent.change(rescrape, { target: { value: '6' } });
    fireEvent.click(rescrapeSave);
    expect(rescrapeMutate).toHaveBeenCalledWith(6, expect.any(Object));
    expect(await screen.findByText('Sources will be scraped every 6 h')).toBeInTheDocument();

    const epg = screen.getByLabelText('Refresh EPG every (hours)');
    expect(epg).toHaveValue(1);
    fireEvent.change(epg, { target: { value: '3' } });
    fireEvent.click(within(screen.getByRole('form', { name: 'Refresh EPG every (hours) form' })).getByRole('button', { name: 'Save' }));
    expect(epgMutate).toHaveBeenCalledWith(3, expect.any(Object));
    expect(await screen.findByText('EPG will refresh every 3 h')).toBeInTheDocument();
  });

  it('reports a failed save in the snackbar', async () => {
    const failingMutate = jest.fn((_value: unknown, options?: MutateOptions) =>
      options?.onError?.(new ApiError({ message: 'Interval must be between 1 and 168 hours', status: 422, kind: 'validation', canRetry: false }))
    );
    (configHooks.useUpdateRescrapeInterval as jest.Mock).mockReturnValue({ mutate: failingMutate, isPending: false });
    renderPage();

    const rescrape = await screen.findByLabelText('Scrape sources every (hours)');
    fireEvent.change(rescrape, { target: { value: '2' } });
    fireEvent.click(within(screen.getByRole('form', { name: 'Scrape sources every (hours) form' })).getByRole('button', { name: 'Save' }));
    expect(await screen.findByText(/Failed to save the scrape interval: Interval must be between 1 and 168 hours/)).toBeInTheDocument();
  });

  it('lists named link formats with a default indicator and row actions', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { level: 2, name: 'Stream link formats' })).toBeInTheDocument();
    expect(screen.getByText('Ace player')).toBeInTheDocument();
    expect(screen.getByText('Local HLS')).toBeInTheDocument();
    expect(screen.getAllByText('Default')).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Make default' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit base URL Local HLS' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete base URL Ace player' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit default link format' })).not.toBeInTheDocument();
  });

  it('shows the built-in default from settings when no named entry is default and edits it in place', async () => {
    const updateLegacy = succeedingMutate();
    (configHooks.useUpdateBaseUrl as jest.Mock).mockReturnValue({ mutate: updateLegacy, isPending: false });
    (baseUrlHooks.useBaseUrls as jest.Mock).mockReturnValue({
      data: [{ id: 2, name: 'Local HLS', pattern: 'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}', is_default: false }],
      isLoading: false,
      error: undefined,
    });
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: 'Edit default link format' }));
    expect(screen.getAllByText('acestream://').length).toBeGreaterThan(0);
    const dialog = screen.getByRole('dialog', { name: 'Edit default link format' });
    fireEvent.change(within(dialog).getByLabelText('Pattern'), { target: { value: 'http://ace:6878/ace/getstream?id=' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save changes' }));
    expect(updateLegacy).toHaveBeenCalledWith('http://ace:6878/ace/getstream?id=', expect.any(Object));
    expect(await screen.findByText('Default link format updated')).toBeInTheDocument();
  });

  it('promotes a non-default entry when its make-default action is used', async () => {
    const patchMutate = succeedingMutate();
    (baseUrlHooks.usePatchBaseUrl as jest.Mock).mockReturnValue({ mutate: patchMutate, isPending: false });
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Make default' }));
    expect(patchMutate).toHaveBeenCalledWith({ id: 2, data: { is_default: true } }, expect.any(Object));
  });

  it('shows a clear duplicate-name message when adding a format returns 409', async () => {
    const createMutate = jest.fn((_variables: unknown, options?: MutateOptions) => {
      options?.onError?.(new ApiError({ message: 'Conflict', status: 409, kind: 'unknown', canRetry: false }));
    });
    (baseUrlHooks.useCreateBaseUrl as jest.Mock).mockReturnValue({ mutate: createMutate, isPending: false });
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: 'Add format' }));
    const dialog = screen.getByRole('dialog', { name: 'Add link format' });
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'Ace player' } });
    fireEvent.change(within(dialog).getByLabelText('Pattern'), { target: { value: 'acestream://' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add base URL' }));
    expect(createMutate).toHaveBeenCalledWith({ name: 'Ace player', pattern: 'acestream://', is_default: false }, expect.any(Object));
    expect(await screen.findByText('A link format named "Ace player" already exists. Choose a different name.')).toBeInTheDocument();
  });

  it('asks before deleting a link format', async () => {
    const deleteMutate = succeedingMutate();
    (baseUrlHooks.useDeleteBaseUrl as jest.Mock).mockReturnValue({ mutate: deleteMutate, isPending: false });
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: 'Delete base URL Local HLS' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete the link format “Local HLS”?' });
    expect(deleteMutate).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(deleteMutate).toHaveBeenCalledWith(2, expect.any(Object)));
  });

  it('recovers from AppID load failures and re-enables the switch after update failures', async () => {
    (configService.getAppId as jest.Mock).mockRejectedValueOnce(new Error('load failed'));
    (configService.updateAppId as jest.Mock).mockRejectedValueOnce(new Error('save failed'));
    renderPage();

    expect(await screen.findByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument();
    expect(screen.getByText(/could not load the appid setting/i)).toBeInTheDocument();
    const appIdToggle = screen.getByRole('checkbox', { name: /use appid in stream links/i });
    fireEvent.click(appIdToggle);
    await waitFor(() => expect(configService.updateAppId).toHaveBeenCalledWith(true));
    await waitFor(() => expect(appIdToggle).not.toBeDisabled());
    expect(appIdToggle).not.toBeChecked();
    expect(screen.getByText(/failed to update appid setting/i)).toBeInTheDocument();
  });
});

import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TestMemoryRouter } from '../testUtils/router';
import Recordings from '../pages/Recordings';
import RecordingSettingsFields from '../components/recordings/RecordingSettingsFields';
import { ApiError } from '../services/apiErrors';
import RecordingPlayback from '../components/recordings/RecordingPlayback';
import { recordingService, type Recording } from '../services/recordingService';
jest.mock('../services/recordingService', () => ({ recordingService: { settings: jest.fn(), configure: jest.fn(), list: jest.fn(), capabilities: jest.fn(), stop: jest.fn(), openPlayback: jest.fn(), closePlayback: jest.fn(), playback: jest.fn() }, recordingFileUrl: () => '/media' }));
const api = jest.mocked(recordingService);
const wrap = (child: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><ThemeProvider theme={createAppTheme('light')}><TestMemoryRouter>{child}</TestMemoryRouter></ThemeProvider></QueryClientProvider>);
beforeEach(() => jest.clearAllMocks());

test('shows recording status and sends Stop without releasing a viewer', async () => {
  const row = { id: 'one', snapshot: { title: 'Evening programme', channel_name: 'One' }, start_time: '2026-10-28T18:00:00Z', end_time: '2026-10-28T19:00:00Z', timezone: 'Europe/Madrid', state: 'recording', gaps: [], files: [] } as unknown as Recording;
  api.list.mockResolvedValue({ items: [row], total: 1 });
  api.capabilities.mockResolvedValue({ enabled: true, available: true } as Awaited<ReturnType<typeof api.capabilities>>);
  api.stop.mockResolvedValue(row);
  wrap(<Recordings />);
  expect(await screen.findByRole('heading', { name: 'Evening programme' })).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Stop recording' }));
  expect(api.stop).not.toHaveBeenCalled();
  fireEvent.click(within(await screen.findByRole('dialog', { name: 'Stop recording?' })).getByRole('button', { name: 'Stop recording' }));
  await waitFor(() => expect(api.stop).toHaveBeenCalledWith('one'));
  expect(api.closePlayback).not.toHaveBeenCalled();
});

test('releases a late playback subscription after the dialog closes', async () => {
  let resolve!: (value: Awaited<ReturnType<typeof api.openPlayback>>) => void;
  api.openPlayback.mockReturnValue(new Promise((done) => { resolve = done; }));
  api.closePlayback.mockResolvedValue(undefined);
  const { unmount } = wrap(<RecordingPlayback recordingId="one" fileId="file" />);
  expect(screen.getByRole('progressbar', { name: 'Preparing recording playback' })).toBeVisible();
  unmount();
  resolve({ id: 'late', state: 'preparing', file_id: 'derivative', message: 'Preparing' });
  await waitFor(() => expect(api.closePlayback).toHaveBeenCalledWith('one', 'late'));
});

 test('shows the actionable storage error when saving recording settings', async () => {
  api.settings.mockResolvedValue({ enabled: false, max_concurrent: 1 });
  const message = 'Recording storage is unavailable. Check the configured directory and mount.';
  api.configure.mockRejectedValue(new ApiError({ message, code: 'RECORDING_STORAGE_UNAVAILABLE', status: 503, kind: 'server', canRetry: true }));
  wrap(<RecordingSettingsFields />);
  fireEvent.click(await screen.findByRole('checkbox', { name: 'Enable recordings' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save recording settings' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(message);
  expect(screen.getByRole('checkbox', { name: 'Enable recordings' })).toBeChecked();
});

test('requires explicit disable confirmation, retains drafts on cancel, and saves once', async () => {
  api.settings.mockResolvedValue({ enabled: true, max_concurrent: 1 });
  api.configure.mockImplementation(async value => value);
  wrap(<RecordingSettingsFields />);
  fireEvent.click(await screen.findByRole('checkbox', { name: 'Enable recordings' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save recording settings' }));
  const dialog = await screen.findByRole('dialog', { name: 'Disable recordings?' });
  expect(dialog).toHaveTextContent('Active recordings will stop and future recordings will be cancelled. Saved files will remain.');
  expect(api.configure).not.toHaveBeenCalled();
  fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
  await waitFor(() => expect(screen.getByRole('checkbox', { name: 'Enable recordings' })).not.toBeChecked());
  expect(api.configure).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Save recording settings' }));
  fireEvent.click(within(await screen.findByRole('dialog', { name: 'Disable recordings?' })).getByRole('button', { name: 'Disable recordings' }));
  await waitFor(() => expect(api.configure).toHaveBeenCalledTimes(1));
  expect(api.configure.mock.calls[0][0]).toEqual({ enabled: false, max_concurrent: 1, min_free_bytes: 2147483648, max_recording_bytes: 107374182400, retention_days: null });
  expect(await screen.findByText('Recording settings saved.')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Save recording settings' })).toBeDisabled();
});

test('enforces the byte, concurrency and retention boundaries before submitting', async () => {
  api.settings.mockResolvedValue({ enabled: false, max_concurrent: 1 });
  wrap(<RecordingSettingsFields />);
  const concurrency = await screen.findByRole('spinbutton', { name: 'Simultaneous recordings' });
  fireEvent.change(concurrency, { target: { value: '5' } });
  expect(screen.getByRole('button', { name: 'Save recording settings' })).toBeDisabled();
  fireEvent.change(concurrency, { target: { value: '2' } });
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Keep free (GiB)' }), { target: { value: '0.01' } });
  expect(screen.getByRole('button', { name: 'Save recording settings' })).toBeDisabled();
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Keep free (GiB)' }), { target: { value: '0.0625' } });
  expect(screen.getByRole('button', { name: 'Save recording settings' })).toBeEnabled();
  fireEvent.click(screen.getByRole('checkbox', { name: 'Automatically delete old, unprotected recordings' }));
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Delete after (days)' }), { target: { value: '3651' } });
  expect(screen.getByRole('button', { name: 'Save recording settings' })).toBeDisabled();
  expect(api.configure).not.toHaveBeenCalled();
});

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
jest.mock('../services/recordingService', () => ({ recordingService: { settings: jest.fn(), configure: jest.fn(), list: jest.fn(), capabilities: jest.fn(), stop: jest.fn(), convert: jest.fn(), edit: jest.fn(), openPlayback: jest.fn(), closePlayback: jest.fn(), playback: jest.fn() }, recordingFileUrl: () => '/media' }));
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

test('loads library, active captures and history as server collections with separate totals', async () => {
  const base = { snapshot: { title: 'Saved programme', channel_name: 'One' }, start_time: '2026-10-28T18:00:00Z', end_time: '2026-10-28T19:00:00Z', timezone: 'Europe/Madrid', gaps: [], files: [] };
  const saved = { ...base, id: 'saved', state: 'completed' } as unknown as Recording;
  const deleted = { ...base, id: 'deleted', state: 'deleted', snapshot: { title: 'Deleted programme', channel_name: 'One' } } as unknown as Recording;
  api.list.mockImplementation(async (_, offset, search, collection) => ({ items: collection === 'history' ? [deleted] : collection === 'upcoming' ? [] : [saved], total: collection === 'library' ? 61 : collection === 'history' ? 1 : 0 }));
  api.capabilities.mockResolvedValue({ enabled: true, available: true } as Awaited<ReturnType<typeof api.capabilities>>);
  wrap(<Recordings />);
  expect(await screen.findByRole('heading', { name: 'Saved programme' })).toBeVisible();
  expect(api.list).toHaveBeenCalledWith('', 0, '', 'library');
  expect(screen.queryByText('Deleted programme')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Go to page 2' }));
  await waitFor(() => expect(api.list).toHaveBeenCalledWith('', 50, '', 'library'));
  fireEvent.click(screen.getByRole('tab', { name: 'History' }));
  expect(await screen.findByRole('heading', { name: 'Deleted programme' })).toBeVisible();
  expect(api.list).toHaveBeenCalledWith('', 0, '', 'history');
  expect(screen.queryByRole('button', { name: 'Play' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('tab', { name: 'Upcoming and active' }));
  expect(await screen.findByText('No upcoming or active recordings. Schedule a programme from its guide or record a channel now.')).toBeVisible();
  expect(api.list).toHaveBeenCalledWith('', 0, '', 'upcoming');
});

test('explains conversion and protection removal, and numbers derivatives with their original part', async () => {
  const file = { state: 'ready', bytes: 1024, reason: null, profile: null, source_artifact_id: null };
  const row = { id: 'saved', revision: 2, protected: true, snapshot: { title: 'Evening programme', channel_name: 'One' }, start_time: '2026-10-28T18:00:00Z', end_time: '2026-10-28T19:00:00Z', timezone: 'UTC', state: 'completed', gaps: [], files: [
    { ...file, id: 'first', kind: 'original' }, { ...file, id: 'second', kind: 'original' }, { ...file, id: 'copy', kind: 'derivative', profile: 'aac', source_artifact_id: 'first' },
  ] } as unknown as Recording;
  api.list.mockResolvedValue({ items: [row], total: 1 });
  api.capabilities.mockResolvedValue({ enabled: true, available: true, mp4_remux: true, aac_conversion: true } as Awaited<ReturnType<typeof api.capabilities>>);
  api.convert.mockResolvedValue(row.files![2]); api.edit.mockResolvedValue(row);
  wrap(<Recordings />);
  expect(await screen.findByText(/Original · part 2/)).toBeVisible();
  expect(screen.getByText(/MP4 · part 1/)).toBeVisible();
  fireEvent.click(screen.getAllByRole('button', { name: 'Prepare MP4' })[0]);
  const confirmation = await screen.findByRole('dialog', { name: 'Prepare an MP4 copy?' });
  expect(confirmation).toHaveTextContent('The original remains available.');
  expect(api.convert).not.toHaveBeenCalled();
  fireEvent.click(within(confirmation).getByRole('button', { name: 'Prepare MP4' }));
  await waitFor(() => expect(api.convert).toHaveBeenCalledWith('saved', 'first', 'remux'));
  fireEvent.click(screen.getByRole('button', { name: 'Remove protection' }));
  const protection = await screen.findByRole('dialog', { name: 'Remove recording protection?' });
  expect(protection).toHaveTextContent('Its files are not deleted now.');
  expect(api.edit).not.toHaveBeenCalled();
  fireEvent.click(within(protection).getByRole('button', { name: 'Cancel' }));
  expect(api.edit).not.toHaveBeenCalled();
});

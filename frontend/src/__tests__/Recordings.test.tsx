import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TestMemoryRouter } from '../testUtils/router';
import Recordings from '../pages/Recordings';
import RecordingPlayback from '../components/recordings/RecordingPlayback';
import { recordingService, type Recording } from '../services/recordingService';
jest.mock('../services/recordingService', () => ({ recordingService: { list: jest.fn(), capabilities: jest.fn(), stop: jest.fn(), openPlayback: jest.fn(), closePlayback: jest.fn(), playback: jest.fn() }, recordingFileUrl: () => '/media' }));
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

import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import LiveTV from '../pages/LiveTV';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import { recordingService } from '../services/recordingService';

const now = new Date();
const future = new Date(now.getTime() + 3600_000);
const programme = { id: 7, epg_channel_id: 10, title: 'Evening documentary', description: 'A programme to record',
  start_time: future.toISOString(), end_time: new Date(now.getTime() + 7200_000).toISOString() };
const channel = { id: 1, name: 'One', is_active: true, epg_source_id: 2, epg_id: 'one', acestream_channels: [{ id: 'stream', is_active: true }] };
const mockCatalog = jest.fn();
const mockPlayer = jest.fn();
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: () => mockCatalog(), useTVChannel: () => ({}) }));
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannels: () => ({ data: { items: [], total: 0 } }) }));
jest.mock('../hooks/useEPG', () => ({ useResolveEPGChannel: () => ({ data: { id: 10 } }), useEPGPrograms: () => ({ data: [programme] }) }));
jest.mock('../components/player/PlayOnMenu', () => ({ __esModule: true, default: () => null }));
jest.mock('../components/player/ChannelPlayerDialog', () => ({ __esModule: true, default: (props: { open: boolean }) => { mockPlayer(props.open); return null; } }));
jest.mock('../services/recordingService', () => ({ recordingService: { create: jest.fn(), currentProgramme: jest.fn() } }));
const service = jest.mocked(recordingService);
function renderPage() {
  return render(<ThemeProvider theme={createAppTheme('light')}><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><TestMemoryRouter><LiveTV /></TestMemoryRouter></QueryClientProvider></ThemeProvider>);
}
beforeEach(() => { jest.clearAllMocks(); mockCatalog.mockReturnValue({ data: [channel] }); });

it('browses upcoming programmes and schedules the selected programme without playback', async () => {
  service.create.mockResolvedValue({ id: 'saved' } as Awaited<ReturnType<typeof service.create>>);
  renderPage();
  fireEvent.click(screen.getByRole('button', { name: 'TV guide for One' }));
  const guide = screen.getByRole('region', { name: 'TV guide for One' });
  if (future.getDate() !== now.getDate()) fireEvent.click(within(guide).getByRole('tab', { name: 'Tomorrow' }));
  fireEvent.click(within(guide).getByRole('button', { name: 'Record Evening documentary' }));
  const dialog = await screen.findByRole('dialog', { name: 'Schedule recording' });
  expect(within(dialog).getByText('Evening documentary')).toBeVisible();
  expect(service.create).not.toHaveBeenCalled();
  fireEvent.click(within(dialog).getByRole('button', { name: 'Schedule' }));
  await waitFor(() => expect(service.create).toHaveBeenCalledWith(expect.objectContaining({
    tv_channel_id: 1, mode: 'schedule', start_time: programme.start_time, end_time: programme.end_time, programme: expect.objectContaining(programme),
  })));
  expect(service.currentProgramme).not.toHaveBeenCalled();
  expect(mockPlayer.mock.calls.every(([open]) => !open)).toBe(true);
});

it('keeps the guide readable but prevents recording when all streams are disabled', () => {
  mockCatalog.mockReturnValue({ data: [{ ...channel, acestream_channels: [{ id: 'stream', is_active: false }] }] });
  renderPage();
  expect(screen.getByRole('button', { name: 'Record One' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'TV guide for One' }));
  expect(screen.getByText('Enable a stream assigned to this TV channel to schedule recordings.')).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Record Evening documentary' })).not.toBeInTheDocument();
  expect(mockPlayer.mock.calls.every(([open]) => !open)).toBe(true);
});

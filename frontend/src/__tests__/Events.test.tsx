import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createAppTheme } from '../theme';
import Events from '../pages/Events';
import { eventService, type SportingEvent } from '../services/eventService';

jest.mock('../services/eventService', () => ({ eventService: { list: jest.fn(), get: jest.fn(), preview: jest.fn(), apply: jest.fn(), update: jest.fn() } }));
jest.mock('../components/player/StreamPlayerDialog', () => ({ __esModule: true, default: ({ open, contentId, onClose }: { open: boolean; contentId: string; onClose: () => void }) => {
  const { Dialog } = jest.requireActual<typeof import('@mui/material')>('@mui/material');
  return <Dialog open={open} PaperProps={{ 'aria-label': 'Event player' }}>{contentId}<button onClick={onClose}>Stop playback</button></Dialog>;
} }));
const service = jest.mocked(eventService);
const event: SportingEvent = {
  id: 'a'.repeat(32), revision: 1, title: 'North United vs South City', sport: 'Football', competition: 'Cup',
  timezone: 'Europe/Madrid', starts_at: '2026-10-24T21:30:00Z', ends_at: null, state: 'scheduled',
  corrected: false, followed: false, archived: false, participants: [], time_notes: '',
  broadcasts: [
    { id: 'es', label: 'Sports One', language: 'Spanish', quality: 'HD', country: 'Spain', source_name: 'Guide', origin: '', content_id: 'a'.repeat(40), compatibility: 'playable', reason: 'AceStream', is_online: null, checked_at: null },
    { id: 'unknown', label: 'DAZN', language: '', quality: '', country: '', source_name: 'Guide', origin: '', content_id: null, compatibility: 'unresolved', reason: 'No stream mapped.', is_online: null, checked_at: null },
  ],
  provenance: [{ source_id: 'guide', source_name: 'Guide', source_kind: 'guide', external_id: '1', updated_at: '2026-10-22T00:00:00Z' }],
};
function renderPage(mode: 'light' | 'dark' = 'light') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><ThemeProvider theme={createAppTheme(mode)}><Events /></ThemeProvider></QueryClientProvider>);
}
beforeEach(() => {
  jest.clearAllMocks();
  service.list.mockResolvedValue({ events: [event], total: 1 });
  service.get.mockResolvedValue(event);
  service.update.mockResolvedValue({ ...event, followed: true, revision: 2 });
  service.preview.mockResolvedValue({ token: 'review', events: [event], warnings: ['Import is not proof of live play or media signal.'] });
  service.apply.mockResolvedValue([event]);
  Object.defineProperty(global.crypto, 'randomUUID', { configurable: true, value: () => 'manual-1' });
});
it.each(['light', 'dark'] as const)('filters, inspects and plays only a compatible source in %s mode', async (mode) => {
  const user = userEvent.setup();
  renderPage(mode);
  await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
  expect(await screen.findByText('No stream mapped. · Guide')).toBeVisible();
  expect(screen.getAllByText('Signal not checked').length).toBe(2);
  expect(screen.queryByRole('button', { name: 'Play DAZN' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Play Sports One' }));
  expect(screen.getByRole('dialog', { name: 'Event player' })).toHaveTextContent('a'.repeat(40));
  await user.click(screen.getByRole('button', { name: 'Stop playback' }));
  await user.click(await screen.findByRole('button', { name: 'Close event details' }));
  await user.type(screen.getByLabelText('Search events'), 'North');
  await waitFor(() => expect(service.list).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'North' })));
});
it('previews manual events without saving until a row is selected', async () => {
  const user = userEvent.setup();
  renderPage();
  await user.click(screen.getByRole('button', { name: 'Add events' }));
  await user.type(screen.getByLabelText(/Event title/), 'New fixture');
  await user.click(screen.getByRole('button', { name: 'Preview events' }));
  expect(await screen.findByRole('button', { name: 'Save selected (0)' })).toBeDisabled();
  expect(service.apply).not.toHaveBeenCalled();
  expect(service.preview).toHaveBeenCalledWith(expect.objectContaining({ observations: [expect.objectContaining({ title: 'New fixture', starts_at: null, state: 'unknown' })] }));
  await user.click(screen.getByRole('checkbox', { name: 'North United vs South City · scheduled' }));
  await user.click(screen.getByRole('button', { name: 'Save selected (1)' }));
  await waitFor(() => expect(service.apply).toHaveBeenCalledWith('review', [event.id]));
});
it('saves following with the current revision', async () => {
  const user = userEvent.setup();
  renderPage();
  await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
  await user.click(await screen.findByRole('button', { name: 'Follow event' }));
  await waitFor(() => expect(service.update).toHaveBeenCalledWith(event.id, { revision: 1, followed: true }));
});
it('shows useful empty and failed-source states', async () => {
  service.list.mockResolvedValue({ events: [], total: 0 });
  renderPage();
  expect(await screen.findByText('No events in this view')).toBeVisible();
  expect(screen.getByText(/Events without a start time appear/)).toBeVisible();
});
it('displays a loading error with retry', async () => {
  service.list.mockRejectedValue(new Error('offline'));
  renderPage();
  expect(await screen.findByText('Events could not be loaded.')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled();
});

it('keeps save errors visible inside event details', async () => {
  service.update.mockRejectedValue(new Error('save failed'));
  const user = userEvent.setup();
  renderPage();
  await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
  await user.click(await screen.findByRole('button', { name: 'Follow event' }));
  expect(await screen.findByRole('alert')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Follow event' })).toBeEnabled();
});

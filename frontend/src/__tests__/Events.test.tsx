import React from 'react';
import { TestMemoryRouter } from '../testUtils/router';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createAppTheme } from '../theme';
import Events from '../pages/Events';
import EventAgenda from '../components/events/EventAgenda';
import channelService from '../services/channelService';
import { eventService, type SportingEvent } from '../services/eventService';

jest.mock('../services/eventService', () => ({ eventService: { list: jest.fn(), get: jest.fn(), preview: jest.fn(), apply: jest.fn(), update: jest.fn(), sources: jest.fn(), previewSource: jest.fn(), updateSource: jest.fn(), deleteSource: jest.fn(), retention: jest.fn(), saveRetention: jest.fn(), mapBroadcast: jest.fn(), artwork: jest.fn(), refreshSources: jest.fn(), providers: jest.fn(), interests: jest.fn(), broadcastTargets: jest.fn(), mapBroadcastTarget: jest.fn() } }));
jest.mock('../services/channelService', () => ({ __esModule: true, default: { getAcestreamChannels: jest.fn() } }));
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
function renderPage(mode: 'light' | 'dark' = 'light', route = '/events') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><ThemeProvider theme={createAppTheme(mode)}><TestMemoryRouter initialEntries={[route]}><Events /></TestMemoryRouter></ThemeProvider></QueryClientProvider>);
}
beforeEach(() => {
  jest.clearAllMocks();
  service.sources.mockResolvedValue([]);
  service.providers.mockResolvedValue({ feeds: [{ id: 'all', name: 'All sports' }, { id: 'automovilismo', name: 'Motorsport' }], leagues: [{ id: 'es.1', name: 'La Liga', timezone: 'Europe/Madrid' }] });
  service.interests.mockResolvedValue({ sports: ['Football', 'Motorsport'], competitions: ['Fórmula 1', 'Premier League'], teams: ['North United'] });
  service.broadcastTargets.mockResolvedValue([]);
  service.mapBroadcastTarget.mockResolvedValue(event);
  service.retention.mockResolvedValue({ ended_days: 0, archived_days: 0 });
  service.saveRetention.mockResolvedValue({ ended_days: 7, archived_days: 30 });
  service.mapBroadcast.mockResolvedValue(event);
  service.previewSource.mockResolvedValue({ token: 'source-review', events: [event], warnings: [] });
  service.list.mockResolvedValue({ events: [event], total: 1 });
  service.get.mockResolvedValue(event);
  service.update.mockResolvedValue({ ...event, followed: true, revision: 2 });
  service.preview.mockResolvedValue({ token: 'review', events: [event], warnings: ['Import is not proof of live play or media signal.'] });
  service.apply.mockResolvedValue([event]);
});
it.each(['light', 'dark'] as const)('filters, inspects and plays only a compatible source in %s mode', async (mode) => {
  const user = userEvent.setup();
  renderPage(mode);
  await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
  expect(screen.queryByText('No stream mapped. · Guide')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Manage event' }));
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
  await user.click(screen.getByLabelText('Add from'));
  await user.click(screen.getByRole('option', { name: 'Create an event' }));
  await user.type(screen.getByLabelText(/Event title/), 'New fixture');
  await user.click(screen.getByRole('button', { name: 'Preview events' }));
  expect(await screen.findByRole('button', { name: 'Save selected (0)' })).toBeDisabled();
  expect(service.apply).not.toHaveBeenCalled();
  expect(service.preview).toHaveBeenCalledWith(expect.objectContaining({ observations: [expect.objectContaining({ title: 'New fixture', starts_at: null, state: 'unknown' })] }));
  await user.click(screen.getByRole('checkbox', { name: 'North United vs South City · scheduled' }));
  await user.click(screen.getByRole('button', { name: 'Save selected (1)' }));
  await waitFor(() => expect(service.apply).toHaveBeenCalledWith('review', [event.id]));
});
it('opens over LAN HTTP and keeps manual identity stable across previews but separate for new events', async () => {
  const original = Object.getOwnPropertyDescriptor(global.crypto, 'randomUUID');
  Object.defineProperty(global.crypto, 'randomUUID', { configurable: true, value: undefined });
  try {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole('button', { name: 'Add events' }));
    await user.click(screen.getByLabelText('Add from'));
    await user.click(screen.getByRole('option', { name: 'Create an event' }));
    await user.type(screen.getByLabelText(/Event title/), 'First fixture');
    await user.click(screen.getByRole('button', { name: 'Preview events' }));
    await screen.findByRole('button', { name: 'Back to input' });
    const firstId = service.preview.mock.calls[0][0].observations[0].external_id;
    expect(firstId).toMatch(/^[a-f0-9]{32}$/);
    await user.click(screen.getByRole('button', { name: 'Back to input' }));
    await user.click(screen.getByLabelText('Add from'));
    await user.click(screen.getByRole('option', { name: 'Create an event' }));
    await user.type(screen.getByLabelText(/Event title/), ' corrected');
    await user.click(screen.getByRole('button', { name: 'Preview events' }));
    await screen.findByRole('button', { name: 'Back to input' });
    expect(service.preview.mock.calls[1][0].observations[0].external_id).toBe(firstId);
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    await user.click(screen.getByRole('button', { name: 'Add events' }));
    await user.click(screen.getByLabelText('Add from'));
    await user.click(screen.getByRole('option', { name: 'Create an event' }));
    await user.type(screen.getByLabelText(/Event title/), 'Second fixture');
    await user.click(screen.getByRole('button', { name: 'Preview events' }));
    await screen.findByRole('button', { name: 'Back to input' });
    expect(service.preview.mock.calls[2][0].observations[0].external_id).not.toBe(firstId);
    expect(service.apply).not.toHaveBeenCalled();
  } finally {
    if (original) Object.defineProperty(global.crypto, 'randomUUID', original);
    else Reflect.deleteProperty(global.crypto, 'randomUUID');
  }
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
  expect(screen.getByText(/Events without a date appear/)).toBeVisible();
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


it('reviews a URL before enabling scheduled refresh and saves explicit retention', async () => {
  const user = userEvent.setup();
  renderPage();
  await user.click(screen.getByRole('button', { name: 'Sources & retention' }));
  expect(await screen.findByText(/No saved schedule URLs/)).toBeVisible();
  await user.clear(screen.getByLabelText('Keep ended events (days)'));
  await user.type(screen.getByLabelText('Keep ended events (days)'), '7');
  await user.click(screen.getByRole('button', { name: 'Save retention' }));
  await waitFor(() => expect(service.saveRetention).toHaveBeenCalledWith({ ended_days: 7, archived_days: 0 }));
  await user.click(screen.getByRole('button', { name: 'Add events' }));
  await user.click(screen.getByLabelText('Add from'));
  await user.click(screen.getByRole('option', { name: 'Load schedule URL' }));
  await user.type(screen.getByLabelText('Schedule URL'), 'https://guide.example/events.json');
  await user.click(screen.getByRole('button', { name: 'Preview events' }));
  expect(await screen.findByRole('button', { name: 'Save selected (0)' })).toBeDisabled();
  expect(service.apply).not.toHaveBeenCalled();
  await user.click(screen.getByRole('checkbox', { name: /Refresh selected events automatically/ }));
  await user.click(screen.getByRole('checkbox', { name: 'North United vs South City · scheduled' }));
  await user.click(screen.getByRole('button', { name: 'Save selected (1)' }));
  await waitFor(() => expect(service.apply).toHaveBeenCalledWith('source-review', [event.id], true));
});

it('requires selecting an exact stream to map an unresolved broadcaster', async () => {
  jest.mocked(channelService.getAcestreamChannels).mockResolvedValue({ total: 1, items: [{ id: 'b'.repeat(40), name: 'DAZN Spain', group: 'Spain', last_seen: '', status: '', is_online: null, epg_update_protected: false }] });
  const user = userEvent.setup();
  renderPage();
  await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
  await user.click(screen.getByRole('button', { name: 'Link DAZN' }));
  expect(screen.getByRole('button', { name: 'Save broadcast mapping' })).toBeDisabled();
  await user.click(screen.getByLabelText('Link to'));
  await user.click(screen.getByRole('option', { name: 'Individual stream' }));
  await user.click(screen.getByRole('combobox', { name: 'Find stream for DAZN' }));
  await user.click(await screen.findByRole('option', { name: 'DAZN Spain · Spain · bbbbbbbb' }));
  await user.click(screen.getByRole('button', { name: 'Save broadcast mapping' }));
  await waitFor(() => expect(service.mapBroadcast).toHaveBeenCalledWith(event.id, 1, 'unknown', 'b'.repeat(40)));
});


it('loads artwork only on request and keeps broadcasts usable after an image failure', async () => {
  service.get.mockResolvedValue({ ...event, has_artwork: true });
  service.artwork.mockRejectedValue(new Error('missing image'));
  const user = userEvent.setup();
  renderPage();
  await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
  expect(service.artwork).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: 'Load event artwork' }));
  expect(await screen.findByText(/Artwork is unavailable/)).toBeVisible();
  expect(screen.getByRole('button', { name: 'Play Sports One' })).toBeEnabled();
});


it('reports raster decode failures and releases the artwork blob on close', async () => {
  const originalCreate = URL.createObjectURL;
  const originalRevoke = URL.revokeObjectURL;
  URL.createObjectURL = jest.fn(() => 'blob:event-artwork');
  URL.revokeObjectURL = jest.fn();
  try {
    service.get.mockResolvedValue({ ...event, has_artwork: true });
    service.artwork.mockResolvedValue(new Blob(['invalid image'], { type: 'image/png' }));
    const user = userEvent.setup();
    const { unmount } = renderPage();
    await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
    await user.click(screen.getByRole('button', { name: 'Load event artwork' }));
    fireEvent.error(await screen.findByRole('img', { name: `Artwork for ${event.title}` }));
    expect(screen.getByText(/Artwork is unavailable/)).toBeVisible();
    unmount();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:event-artwork');
  } finally {
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
  }
});

it('starts with providers, previews mixed interests again before saving, and keeps the 14-day window', async () => {
  service.previewSource.mockResolvedValue({ token: 'provider-review', events: [event], warnings: [], available_interests: { sports: ['Motorsport'], competitions: ['Premier League'], teams: ['North United'] } });
  const user = userEvent.setup();
  renderPage();
  await user.click(screen.getByRole('button', { name: 'Add events' }));
  expect(screen.getByLabelText('Provider')).toHaveTextContent('Fútbol en la TV');
  expect(screen.getByLabelText('Import window')).toHaveTextContent('Next 14 days');
  await user.click(screen.getByRole('button', { name: 'Preview events' }));
  await screen.findByRole('button', { name: 'Save source without events' });
  await user.click(screen.getByLabelText('Import: Competitions'));
  await user.click(await screen.findByRole('option', { name: 'Premier League' }));
  await user.click(screen.getByLabelText('Import: Teams'));
  await user.click(await screen.findByRole('option', { name: 'North United' }));
  expect(screen.getByRole('button', { name: 'Save source without events' })).toBeDisabled();
  await user.click(screen.getByRole('button', { name: 'Update preview with interests' }));
  await waitFor(() => expect(service.previewSource).toHaveBeenLastCalledWith(expect.objectContaining({ provider_options: expect.objectContaining({ window_days: 14, interests: { sports: [], competitions: ['Premier League'], teams: ['North United'] } }) })));
  await user.click(screen.getByRole('checkbox', { name: 'Select all shown events' }));
  await user.click(screen.getByRole('button', { name: 'Save selected (1)' }));
  await waitFor(() => expect(service.apply).toHaveBeenCalledWith('provider-review', [event.id], false));
});

it('links a differently named regional TV channel and displays TV or EPG destinations', async () => {
  const target = { id: 7, kind: 'tv' as const, name: 'Spanish Sports', country: 'es', source_name: '' };
  service.broadcastTargets.mockResolvedValue([target]);
  service.get.mockResolvedValue({ ...event, broadcasts: [{ ...event.broadcasts[1], target }] });
  const user = userEvent.setup();
  renderPage();
  await user.click(await screen.findByRole('button', { name: 'View broadcasts for North United vs South City' }));
  expect(screen.getByRole('link', { name: 'DAZN' })).toHaveAttribute('href', './tv-channels/7');
  await user.click(screen.getByRole('button', { name: 'Manage event' }));
  await user.click(screen.getByRole('button', { name: 'Link DAZN' }));
  await user.click(screen.getByLabelText('Find channel for DAZN'));
  await user.click(await screen.findByRole('option', { name: /Spanish Sports/ }));
  await user.click(screen.getByRole('button', { name: 'Save broadcast mapping' }));
  await waitFor(() => expect(service.mapBroadcastTarget).toHaveBeenCalledWith(event.id, 1, 'unknown', target));
});

it('combines displayed competition and sport interests without requiring both', async () => {
  const user = userEvent.setup();
  renderPage();
  expect(screen.queryByLabelText('Sports')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Filter events' }));
  await user.click(screen.getByLabelText('Sports'));
  await user.click(await screen.findByRole('option', { name: 'Motorsport' }));
  await user.click(screen.getByLabelText('Competitions'));
  await user.click(await screen.findByRole('option', { name: 'Premier League' }));
  await waitFor(() => expect(service.list).toHaveBeenLastCalledWith(expect.objectContaining({ window_days: 14, interests: JSON.stringify({ sports: ['Motorsport'], competitions: ['Premier League'], teams: [] }) })));
  await user.click(screen.getByRole('button', { name: 'Filter events (2)' }));
  expect(screen.queryByLabelText('Sports')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Filter events (2)' })).toHaveAttribute('aria-expanded', 'false');
});

it('groups local dates while preserving date-only and unknown schedules', () => {
  render(<EventAgenda events={[
    { ...event, id: 'timed', title: 'Late race', starts_at: '2026-10-24T23:30:00Z' },
    { ...event, id: 'date', title: 'Date-only race', starts_at: null, scheduled_date: '2026-10-24' },
    { ...event, id: 'unknown', title: 'Unannounced race', starts_at: null, scheduled_date: null },
  ]} zone="Europe/Madrid" today="2026-10-25" onSelect={jest.fn()} />);
  const sections = screen.getAllByRole('region');
  expect(sections[0]).toHaveTextContent('Date-only race');
  expect(sections[0]).toHaveTextContent('Time TBC');
  expect(sections[0]).not.toHaveTextContent('Late race');
  expect(sections[1]).toHaveTextContent('Today');
  expect(sections[1]).toHaveTextContent('Late race');
  expect(sections[2]).toHaveAccessibleName('Date to be confirmed');
  expect(sections[2]).toHaveTextContent('Unannounced race');
});

it('changes the date scope without exposing management controls', async () => {
  const user = userEvent.setup();
  renderPage();
  await user.click(screen.getByLabelText('When'));
  await user.click(screen.getByRole('option', { name: 'Choose a date' }));
  fireEvent.change(screen.getByLabelText('Event date'), { target: { value: '2026-11-01' } });
  await waitFor(() => expect(service.list).toHaveBeenLastCalledWith(expect.objectContaining({ day: '2026-11-01', upcoming: false, window_days: undefined })));
  await user.click(await screen.findByRole('button', { name: `View broadcasts for ${event.title}` }));
  expect(await screen.findByRole('heading', { name: 'Where to watch' })).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Correct schedule' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Archive event' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Manage event' }));
  expect(screen.getByRole('button', { name: 'Correct schedule' })).toBeVisible();
  expect(screen.getByRole('button', { name: 'Archive event' })).toBeVisible();
});

it('opens a dashboard deep link and handles archived or missing events', async () => {
  service.get.mockResolvedValue({ ...event, archived: true });
  const { unmount } = renderPage('light', `/events?event=${event.id}`);
  expect(await screen.findByText('This event is archived. Close details to return to the agenda.')).toBeVisible();
  expect(service.get).toHaveBeenCalledWith(event.id);
  fireEvent.click(screen.getByRole('button', { name: 'Close event details' }));
  await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Event details' })).not.toBeInTheDocument());
  unmount();
  service.get.mockRejectedValue(new Error('Not found'));
  renderPage('light', '/events?event=missing');
  expect(await screen.findByText(/The event may have been removed/)).toBeVisible();
  expect(screen.getByRole('button', { name: 'Close event details' })).toBeVisible();
});


it('confirms source removal and keeps imported events', async () => {
  const user = userEvent.setup();
  service.sources.mockResolvedValue([{ id: 'source', revision: 2, last_attempt: null, last_success: null, last_result: null, name: 'Football guide', origin: 'example.org', enabled: true, reviewed: 1, format: 'event_import', timezone: 'Europe/Madrid' }]);
  service.deleteSource.mockResolvedValue(undefined);
  renderPage();
  await user.click(screen.getByRole('button', { name: 'Sources & retention' }));
  await user.click(await screen.findByRole('button', { name: 'Delete source' }));
  expect(screen.getByText(/Imported events, manual corrections and channels will be kept/)).toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(service.deleteSource).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: 'Delete source' }));
  const dialog = screen.getByRole('dialog');
  await user.click(within(dialog).getByRole('button', { name: 'Delete source' }));
  await waitFor(() => expect(service.deleteSource).toHaveBeenCalledWith('source', 2));
});

it('shows matched guide programmes and assigned TV channel links', async () => {
  service.get.mockResolvedValue({ ...event, epg_matches: [{ program_id: 7, title: 'Cup: North United - South City', starts_at: event.starts_at!, ends_at: '2026-10-24T23:30:00Z', epg_channel: { kind: 'epg', id: 3, name: 'Guide Sports', source_name: 'Local guide' }, tv_channel: { kind: 'tv', id: 4, name: 'Sports TV' } }] });
  renderPage('dark', `/events?event=${event.id}`);
  expect(await screen.findByText('Matching guide programmes')).toBeVisible();
  expect(screen.getByRole('link', { name: /Guide Sports/ })).toHaveAttribute('href', '/epg/channels/3');
  expect(screen.getByRole('link', { name: 'Open Sports TV' })).toHaveAttribute('href', '/tv-channels/4');
});

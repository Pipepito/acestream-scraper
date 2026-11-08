jest.mock('../components/recordings/RecordButton', () => ({ __esModule: true, default: () => <span>Recordings</span> }));
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { TestMemoryRouter as MemoryRouter } from '../testUtils/router';
import { ThemeProvider } from '@mui/material/styles';
import LiveTV from '../pages/LiveTV';
import { createAppTheme } from '../theme';

const mockSend = jest.fn();
const mockPlayers = jest.fn();
jest.mock('../hooks/useRemotePlayers', () => ({
  useRemotePlayers: () => mockPlayers(),
  usePlayOnRemotePlayer: () => ({ mutateAsync: mockSend }),
}));
const mockCatalog = jest.fn();
const mockTVChannel = jest.fn();
const mockPages = jest.fn();
const mockNowNext = jest.fn();
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelPages: (...args: unknown[]) => { const result = mockCatalog(...args); return { ...result, data: result.data ? { pages: [{ items: result.data, total: result.data.length }] } : undefined }; }, useTVChannel: (id: number) => mockTVChannel(id) }));
jest.mock('../hooks/useStreamPages', () => ({ useStreamPages: (...args: unknown[]) => mockPages(...args) }));
jest.mock('../hooks/useNowNext', () => ({ useNowNext: () => mockNowNext() }));
jest.mock('../components/player/ChannelGuide', () => ({ __esModule: true, default: () => <div>Guide</div> }));
jest.mock('../components/player/ChannelPlayerDialog', () => ({ __esModule: true, default: ({ open, title }: { open: boolean; title: string }) => open ? <div role="dialog" aria-label={title} /> : null }));
jest.mock('../services/eventService', () => ({ eventService: { list: jest.fn() } }));
import { eventService } from '../services/eventService';

const channels = (count: number) => Array.from({ length: count }, (_, i) => ({ id: i + 1, name: `Channel ${i + 1}`, is_active: true, acestream_channels: [{ id: `s${i + 1}`, is_active: true, is_online: true }] }));
const pages = (items: Array<Record<string, unknown>>, total: number, extra: Record<string, unknown> = {}) => ({
  data: { pages: [{ items, total }], pageParams: [1] }, fetchNextPage: jest.fn(), hasNextPage: items.length < total, isFetchingNextPage: false, isLoading: false, isError: false, refetch: jest.fn(), ...extra,
});
const renderPage = (route = '/live-tv') => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter initialEntries={[route]}><ThemeProvider theme={createAppTheme('light')}><LiveTV /></ThemeProvider></MemoryRouter></QueryClientProvider>);

beforeEach(() => {
  jest.clearAllMocks();
  mockPlayers.mockReturnValue({ data: [{ id: 7, name: 'Living room', kind: 'vlc' }] });
  mockSend.mockResolvedValue({ warnings: [] });
  mockTVChannel.mockReturnValue({});
  mockNowNext.mockReturnValue({ data: new Map() });
  mockCatalog.mockReturnValue({ data: [
    { id: 1, name: 'Watchable', is_active: true, acestream_channels: [{ id: 'one', is_active: true, is_online: true }] },
    { id: 2, name: 'Empty channel', is_active: true, acestream_channels: [] },
    { id: 3, name: 'Inactive channel', is_active: false, acestream_channels: [{ id: 'two', is_active: true, is_online: true }] },
  ] });
  mockPages.mockReturnValue(pages([{ id: 'raw', name: 'Independent', is_online: true, tv_channel_id: null }], 1));
  jest.mocked(eventService.list).mockResolvedValue({ total: 1, events: [{ id: 'e1', title: 'Derby', competition: 'Liga', sport: 'Football', starts_at: new Date().toISOString(), state: 'scheduled', participants: [], followed: false, archived: false, corrected: false, revision: 1, timezone: 'UTC', ends_at: null, time_notes: '', provenance: [],
    broadcasts: [{ id: 'b', label: 'DAZN 1', target: { kind: 'tv', id: 1, name: 'DAZN 1', country: '', source_name: '' }, compatibility: 'linked', language: '', quality: '', country: '', source_name: '', origin: '', content_id: null, reason: '' },
      { id: 'c', label: 'HBO', target: null, compatibility: 'unresolved', language: '', quality: '', country: '', source_name: '', origin: '', content_id: null, reason: '' }] }] } as never);
});

it('shows only active TV channels with streams in one unpaginated list', () => {
  mockCatalog.mockReturnValue({ data: channels(40) });
  renderPage();
  expect(screen.getAllByRole('button', { name: /^Watch Channel/ })).toHaveLength(40);
  expect(screen.queryByRole('navigation', { name: /pagination/i })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'TV channels', pressed: true })).toBeInTheDocument();
});

it('hides channels without streams or inactive and highlights the playing row', () => {
  mockTVChannel.mockReturnValue({ data: { id: 1, name: 'Watchable', acestream_channels: [{ id: 'one' }] } });
  renderPage('/live-tv?channel=1');
  expect(screen.getByRole('button', { name: 'Watch Watchable' })).toBeEnabled();
  expect(screen.queryByText('Empty channel')).not.toBeInTheDocument();
  expect(screen.queryByText('Inactive channel')).not.toBeInTheDocument();
  expect(screen.getByRole('article', { current: true })).toHaveTextContent('Watchable');
  expect(screen.getByRole('dialog', { name: 'Watchable' })).toBeInTheDocument();
});

it('switches to streams mode, loads more on request and plays a stream', () => {
  const fetchNextPage = jest.fn();
  mockPages.mockReturnValue(pages([{ id: 'raw', name: 'Independent', is_online: true, tv_channel_id: null }], 120, { fetchNextPage }));
  renderPage();
  fireEvent.click(screen.getByRole('button', { name: 'Streams' }));
  expect(screen.getByRole('button', { name: 'Streams', pressed: true })).toBeInTheDocument();
  expect(mockPages).toHaveBeenLastCalledWith(expect.objectContaining({ onlineOnly: true, search: '' }));
  expect(screen.getByText('Showing 1 of 120')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Show more streams' }));
  expect(fetchNextPage).toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Watch Independent' }));
  expect(screen.getByRole('dialog', { name: 'Independent' })).toBeInTheDocument();
});

it('opens streams mode from the URL and drops the online filter when the switch is off', () => {
  renderPage('/live-tv?list=streams');
  expect(screen.getByRole('button', { name: 'Streams', pressed: true })).toBeInTheDocument();
  expect(mockPages).toHaveBeenLastCalledWith(expect.objectContaining({ onlineOnly: true }));
  fireEvent.click(screen.getByRole('checkbox', { name: 'Online only' }));
  expect(mockPages).toHaveBeenLastCalledWith(expect.objectContaining({ onlineOnly: false }));
  fireEvent.change(screen.getByRole('searchbox', { name: 'Find a stream' }), { target: { value: 'sport' } });
  expect(mockPages).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'sport' }));
});

it('keeps the TV list available when streams fail, and shows loading and empty states', () => {
  const refetch = jest.fn();
  mockPages.mockReturnValue(pages([], 0, { isError: true, refetch }));
  let view = renderPage('/live-tv?list=streams');
  expect(screen.getByText('Unable to load streams.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  expect(refetch).toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'TV channels' }));
  expect(screen.getByRole('button', { name: 'Watch Watchable' })).toBeEnabled();
  view.unmount();
  mockPages.mockReturnValue(pages([], 0, { isLoading: true }));
  view = renderPage('/live-tv?list=streams');
  expect(screen.getByRole('progressbar', { name: 'Loading streams' })).toBeInTheDocument();
  view.unmount();
  mockPages.mockReturnValue(pages([], 0));
  mockCatalog.mockReturnValue({ data: [] });
  renderPage('/live-tv?list=streams');
  expect(screen.getByText('No online streams.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'TV channels' }));
  expect(screen.getByText(/No channels have an online stream yet/)).toBeInTheDocument();
});

it('events mode offers Watch for linked broadcasters and Link for the rest', async () => {
  renderPage('/live-tv?list=events');
  expect(await screen.findByText('Derby')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Link HBO' })).toHaveAttribute('href', expect.stringContaining('/events?event=e1'));
  fireEvent.click(screen.getByRole('button', { name: 'Watch DAZN 1' }));
  await waitFor(() => expect(mockTVChannel).toHaveBeenLastCalledWith(1));
  expect(screen.getByRole('button', { name: 'TV channels', pressed: true })).toBeInTheDocument();
});

it.each([['Watchable', 'one', '/live-tv'], ['Independent', 'raw', '/live-tv?list=streams']])('sends %s directly without opening the web player', async (title, contentId, route) => {
  renderPage(route);
  fireEvent.click(screen.getByRole('button', { name: `Send to player ${title}` }));
  fireEvent.click(screen.getByRole('menuitem', { name: 'Living room (VLC)' }));
  await waitFor(() => expect(mockSend).toHaveBeenCalledWith({ id: 7, contentId, title }));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(await screen.findByText(`Sent ${title} to Living room.`)).toBeInTheDocument();
});

it('offers setup when no external players are saved', () => {
  mockPlayers.mockReturnValue({ data: [] });
  renderPage();
  fireEvent.click(screen.getByRole('button', { name: 'Send to player Watchable' }));
  expect(screen.getByRole('menuitem', { name: /Add a player/ })).toHaveAttribute('href', '/integrations/remote-players');
});

it('reports a failed send without opening the web player', async () => {
  mockSend.mockRejectedValue(new Error('offline'));
  renderPage();
  fireEvent.click(screen.getByRole('button', { name: 'Send to player Watchable' }));
  fireEvent.click(screen.getByRole('menuitem', { name: 'Living room (VLC)' }));
  expect(await screen.findByText('Could not reach the player.')).toBeInTheDocument();
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('shows the batched now and next programme for a channel', () => {
  mockNowNext.mockReturnValue({ data: new Map([[1, { tv_channel_id: 1, epg_channel_id: 5, now: { title: 'Live match', start: new Date(Date.now() - 600_000).toISOString(), end: new Date(Date.now() + 600_000).toISOString() }, next: { title: 'Highlights', start: new Date(Date.now() + 600_000).toISOString(), end: new Date(Date.now() + 1_200_000).toISOString() } }]]) });
  renderPage();
  const row = screen.getByRole('article', { name: 'Watchable' });
  expect(within(row).getByText(/Now · Live match/)).toBeInTheDocument();
  expect(within(row).getByText(/Next · .* · Highlights/)).toBeInTheDocument();
});


it('hides offline and unchecked channels, shows returning streams, and preserves playback across filtering', () => {
  const online = { id: 1, name: 'Playing', is_active: true, acestream_channels: [{ id: 'one', is_active: true, is_online: true }] };
  const offline = { id: 2, name: 'Offline TV', is_active: true, acestream_channels: [{ id: 'two', is_active: true, is_online: false }] };
  const unknown = { id: 3, name: 'Unchecked TV', is_active: true, acestream_channels: [{ id: 'three', is_active: true, is_online: null }] };
  mockCatalog.mockReturnValue({ data: [online, offline, unknown] });
  mockTVChannel.mockReturnValue({ data: online });
  renderPage('/live-tv?channel=1');
  expect(screen.queryByRole('button', { name: 'Watch Offline TV' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Watch Unchecked TV' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('checkbox', { name: 'Online only' }));
  expect(screen.getByRole('button', { name: 'Watch Offline TV' })).toBeEnabled();
  expect(screen.getByRole('dialog', { name: 'Playing' })).toBeInTheDocument();
  mockCatalog.mockReturnValue({ data: [online, { ...offline, acestream_channels: [{ id: 'two', is_active: true, is_online: true }] }, unknown] });
  fireEvent.click(screen.getByRole('checkbox', { name: 'Online only' }));
  expect(screen.getByRole('button', { name: 'Watch Offline TV' })).toBeEnabled();
  expect(screen.getByRole('dialog', { name: 'Playing' })).toBeInTheDocument();
});

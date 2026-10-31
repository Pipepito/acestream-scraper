import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { Route, Routes, useLocation } from 'react-router-dom';
import UpcomingEvents from '../components/overview/UpcomingEvents';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import { DASHBOARD_EVENTS_KEY, readEventPreferences } from '../hooks/useDashboardEvents';
import { eventService, type SportingEvent } from '../services/eventService';

jest.mock('../services/eventService', () => ({ eventService: { list: jest.fn(), interests: jest.fn() } }));
const service = jest.mocked(eventService);
const event: SportingEvent = { id: 'live', revision: 1, title: 'Grand Prix', timezone: 'UTC', starts_at: '2026-10-26T12:00:00Z', state: 'live', broadcasts: [], provenance: [], followed: true, archived: false, corrected: false, sport: 'Motorsport', competition: 'Formula 1' };
function Destination() { return <div>{useLocation().search}</div>; }
function mount(mode: 'light' | 'dark' = 'light') {
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return { cache, ...render(<QueryClientProvider client={cache}><ThemeProvider theme={createAppTheme(mode)}><TestMemoryRouter><Routes><Route path="/" element={<UpcomingEvents />} /><Route path="/events" element={<Destination />} /></Routes></TestMemoryRouter></ThemeProvider></QueryClientProvider>) };
}
async function choose(name: string) {
  fireEvent.mouseDown(screen.getByLabelText('Events to show'));
  fireEvent.click(await screen.findByRole('option', { name }));
}
beforeEach(() => {
  jest.clearAllMocks(); localStorage.clear();
  service.list.mockResolvedValue({ events: [event, { ...event, id: 'tbc', title: 'Next race', state: 'scheduled', starts_at: null, scheduled_date: '2026-10-27' }], total: 2 });
  service.interests.mockResolvedValue({ sports: ['Motorsport'], competitions: ['Formula 1'], teams: [] });
});

it.each(['light', 'dark'] as const)('preserves server ranking, reports dates honestly and opens event details in %s mode', async mode => {
  mount(mode);
  expect(screen.getByText('Loading upcoming events…')).toBeVisible();
  const buttons = await screen.findAllByRole('button', { name: /^View broadcasts/ });
  expect(buttons.map(button => button.textContent)).toEqual(['Grand Prix', 'Next race']);
  expect(screen.getByText('Time TBC')).toBeVisible();
  expect(screen.getByText('Live · reported')).toBeVisible();
  expect(service.list).toHaveBeenCalledWith(expect.objectContaining({ selection: 'dashboard', limit: 6, window_days: 7, followed: false }));
  expect(service.interests).not.toHaveBeenCalled();
  fireEvent.click(buttons[0]);
  expect(screen.getByText(/^\?event=live&zone=/)).toBeVisible();
});

it('remembers following without turning an empty result into all events', async () => {
  service.list.mockResolvedValue({ events: [], total: 0 });
  const page = mount();
  await choose('Following');
  expect(await screen.findByText(/No followed events are coming up/)).toBeVisible();
  expect(service.list).toHaveBeenLastCalledWith(expect.objectContaining({ followed: true }));
  page.unmount();
  mount();
  expect(await screen.findByText(/No followed events are coming up/)).toBeVisible();
  expect(readEventPreferences().view).toBe('following');
  fireEvent.click(screen.getByRole('button', { name: 'Show all upcoming' }));
  expect(await screen.findByText('No live or upcoming events in the next seven days.')).toBeVisible();
});

it('requires explicit interests, saves typed choices and validates timezone', async () => {
  const user = userEvent.setup();
  mount();
  await screen.findByText('Grand Prix');
  const calls = service.list.mock.calls.length;
  await choose('My interests');
  expect(screen.getByText(/Choose a sport, competition or team/)).toBeVisible();
  expect(service.list).toHaveBeenCalledTimes(calls);
  await user.click(screen.getByRole('button', { name: 'Choose interests' }));
  await user.type(screen.getByRole('combobox', { name: 'Sports' }), 'Motorsport{Enter}');
  await waitFor(() => expect(service.list).toHaveBeenLastCalledWith(expect.objectContaining({ interests: JSON.stringify({ sports: ['Motorsport'], competitions: [], teams: [] }) })));
  const zone = screen.getByRole('textbox', { name: 'Display timezone' });
  fireEvent.change(zone, { target: { value: 'No/Zone' } }); fireEvent.blur(zone);
  expect(screen.getByText('Use a timezone such as Europe/Madrid')).toBeVisible();
  fireEvent.change(zone, { target: { value: 'Europe/Madrid' } }); fireEvent.blur(zone);
  await waitFor(() => expect(service.list).toHaveBeenLastCalledWith(expect.objectContaining({ zone: 'Europe/Madrid' })));
  expect(readEventPreferences()).toMatchObject({ view: 'interests', zone: 'Europe/Madrid', interests: { sports: ['Motorsport'] } });
});

it('keeps query failures distinct from empty events and retries', async () => {
  service.list.mockRejectedValueOnce(new Error('Offline'));
  mount();
  expect(await screen.findByRole('alert')).toHaveTextContent('Upcoming events could not be loaded.');
  expect(screen.queryByText(/No live or upcoming/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Retry events' }));
  expect(await screen.findByText('Grand Prix')).toBeVisible();
});

it('refreshes after shared event changes and hides stale claims if refresh fails', async () => {
  const { cache } = mount();
  await screen.findByText('Grand Prix');
  service.list.mockRejectedValue(new Error('Offline'));
  await act(async () => { await cache.invalidateQueries({ queryKey: ['events'] }); });
  expect(await screen.findByRole('alert')).toHaveTextContent('Upcoming events could not be loaded.');
  expect(screen.queryByText('Grand Prix')).not.toBeInTheDocument();
});

it.each(['not-json', '{"version":2}', JSON.stringify({ version: 1, view: 'all', zone: 'Invalid', interests: {} }), JSON.stringify({ version: 1, view: 'all', zone: 'UTC', interests: { sports: [4], competitions: [], teams: [] } })])('falls back safely for malformed preferences: %s', value => {
  localStorage.setItem(DASHBOARD_EVENTS_KEY, value);
  expect(readEventPreferences()).toMatchObject({ version: 1, view: 'all', interests: { sports: [], competitions: [], teams: [] } });
});

it('works when browser storage is unavailable', async () => {
  const read = jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('Denied'); });
  const write = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('Denied'); });
  try {
    mount(); await screen.findByText('Grand Prix');
    await choose('Following');
    await waitFor(() => expect(service.list).toHaveBeenLastCalledWith(expect.objectContaining({ followed: true })));
  } finally { read.mockRestore(); write.mockRestore(); }
});

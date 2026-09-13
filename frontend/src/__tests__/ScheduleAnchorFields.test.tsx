import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ScheduleAnchorFields from '../components/ScheduleAnchorFields';
import { getScheduleAnchors, saveScheduleAnchors } from '../services/configService';

jest.mock('../services/configService', () => ({ getScheduleAnchors: jest.fn(), saveScheduleAnchors: jest.fn() }));
const initial = { timezone: 'UTC', url_scraping: null, epg_refresh: null, channel_status: null };
const renderFields = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><ScheduleAnchorFields /></QueryClientProvider>);

beforeEach(() => jest.resetAllMocks());

it('loads, edits and saves anchors without changing intervals', async () => {
  (getScheduleAnchors as jest.Mock).mockResolvedValue(initial);
  (saveScheduleAnchors as jest.Mock).mockImplementation(async value => value);
  renderFields();
  const timezone = await screen.findByLabelText(/Schedule timezone/);
  fireEvent.change(timezone, { target: { value: 'Europe/Madrid' } });
  fireEvent.change(screen.getByLabelText('Scrape sources start time'), { target: { value: '03:15' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save start times' }));
  expect(await screen.findByText('Schedule start times saved.')).toBeInTheDocument();
  expect(saveScheduleAnchors).toHaveBeenCalledWith({ ...initial, timezone: 'Europe/Madrid', url_scraping: '03:15' }, expect.anything());
  fireEvent.change(screen.getByLabelText('Scrape sources start time'), { target: { value: '' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save start times' }));
  await waitFor(() => expect(saveScheduleAnchors).toHaveBeenLastCalledWith({ ...initial, timezone: 'Europe/Madrid' }, expect.anything()));
});

it('shows a load error and allows retry', async () => {
  (getScheduleAnchors as jest.Mock).mockRejectedValueOnce(new Error('Unavailable')).mockResolvedValue(initial);
  renderFields();
  fireEvent.click(await screen.findByRole('button', { name: 'Retry' }));
  expect(await screen.findByLabelText(/Schedule timezone/)).toHaveValue('UTC');
});

it('keeps the draft after a failed save', async () => {
  (getScheduleAnchors as jest.Mock).mockResolvedValue(initial);
  (saveScheduleAnchors as jest.Mock).mockRejectedValue(new Error('Cannot save'));
  renderFields();
  fireEvent.change(await screen.findByLabelText(/Schedule timezone/), { target: { value: 'Europe/Madrid' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save start times' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong. Try again.');
  expect(screen.getByLabelText(/Schedule timezone/)).toHaveValue('Europe/Madrid');
});

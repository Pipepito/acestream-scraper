import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SearchBroadcastStatus from '../components/SearchBroadcastStatus';
import { searchService } from '../services/searchService';

jest.mock('../services/searchService', () => ({ searchService: { checkBroadcast: jest.fn() } }));
const checkBroadcast = searchService.checkBroadcast as jest.Mock;

const renderStatus = (status?: number) => render(
  <QueryClientProvider client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}>
    <SearchBroadcastStatus channel={{ id: 'a'.repeat(40), name: 'Example', categories: [], status, availability: 1, availability_updated_at: 1700000000 }} />
  </QueryClientProvider>
);

beforeEach(() => jest.clearAllMocks());

it.each([[2, 'available'], [1, 'uncertain'], [undefined, 'unknown']])('keeps catalogue status %s separate from live checks', (status, label) => {
  renderStatus(status as number | undefined);
  expect(screen.getByText(`Catalogue: ${label}`)).toBeInTheDocument();
  expect(screen.getByText('Broadcast not checked')).toBeInTheDocument();
  expect(screen.getByText(/^Updated /)).toBeInTheDocument();
  expect(checkBroadcast).not.toHaveBeenCalled();
});

it.each([true, false])('reports observed broadcast result %s only after a check', async (online) => {
  let resolve: (value: unknown) => void = () => undefined;
  checkBroadcast.mockReturnValue(new Promise((done) => { resolve = done; }));
  renderStatus(2);
  fireEvent.click(screen.getByRole('button', { name: 'Check broadcast for Example' }));
  expect(await screen.findByText('Checking broadcast…')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Check broadcast for Example' })).toBeDisabled();
  resolve({ is_online: online, message: 'Probe result', last_checked: new Date().toISOString() });
  expect(await screen.findByText(online ? 'Broadcast detected' : 'No broadcast detected')).toBeInTheDocument();
  expect(screen.getByText('Catalogue: available')).toBeInTheDocument();
  expect(screen.getByText(/^Checked /)).toBeInTheDocument();
  expect(checkBroadcast).toHaveBeenCalledWith('a'.repeat(40));
});

it('shows a failed request and permits retry without claiming offline', async () => {
  checkBroadcast.mockRejectedValueOnce(new Error('Engine unavailable')).mockResolvedValueOnce({ is_online: true, last_checked: new Date().toISOString() });
  renderStatus();
  fireEvent.click(screen.getByRole('button', { name: 'Check broadcast for Example' }));
  expect(await screen.findByText(/Check failed:/)).toBeInTheDocument();
  expect(screen.queryByText('No broadcast detected')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Check broadcast for Example' }));
  expect(await screen.findByText('Broadcast detected')).toBeInTheDocument();
});

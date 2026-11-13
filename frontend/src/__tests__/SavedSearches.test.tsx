import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TestMemoryRouter as MemoryRouter } from '../testUtils/router';
import SavedSearches from '../components/imports/SavedSearches';
import { savedSearchService as service, SavedSearch } from '../services/savedSearchService';
jest.mock('../services/savedSearchService');
const api = jest.mocked(service);
const row: SavedSearch = { id: 1, revision: 1, name: 'Sports', query: 'Sport ES', category: '', refresh_enabled: false, created_at: '', updated_at: '' };
function setup() { return render(<ThemeProvider theme={createAppTheme('light')}><MemoryRouter><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><SavedSearches /></QueryClientProvider></MemoryRouter></ThemeProvider>); }
beforeEach(() => { jest.resetAllMocks(); api.list.mockResolvedValue({ items: [row], total: 1 }); });
it('runs a paused search without enabling its automatic refresh', async () => {
  api.run.mockResolvedValue({ ...row, run_state: 'waiting', run_id: 'run' });
  setup();
  fireEvent.click(await screen.findByRole('button', { name: 'Run now' }));
  await waitFor(() => expect(api.run).toHaveBeenCalledWith(row, undefined));
  expect(api.save).not.toHaveBeenCalled();
});
it('disables duplicate run requests while waiting', async () => {
  api.list.mockResolvedValue({ items: [{ ...row, run_state: 'waiting' }], total: 1 });
  setup();
  expect(await screen.findByRole('button', { name: 'Waiting' })).toBeDisabled();
});
it('creates configuration only with refresh off by default', async () => {
  api.save.mockResolvedValue(row);
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Create search' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), { target: { value: 'Sports' } });
  fireEvent.change(screen.getByRole('textbox', { name: 'Query' }), { target: { value: 'Sport ES' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));
  await waitFor(() => expect(api.save).toHaveBeenCalledWith({ name: 'Sports', query: 'Sport ES', category: '', refresh_enabled: false }, undefined));
  expect(api.run).not.toHaveBeenCalled();
  expect(api.preview).not.toHaveBeenCalled();
});

it('preserves the reviewed revision and draft across refresh, guards pending save, and confirms discard', async () => {
  const { default: SavedSearchDialog } = await import('../components/imports/SavedSearchDialog');
  const { act, within } = await import('@testing-library/react');
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const onClose = jest.fn();
  let fail!: (error: Error) => void;
  api.save.mockImplementation(() => new Promise((_, reject) => { fail = reject; }));
  const tree = (revision: number) => <ThemeProvider theme={createAppTheme('light')}><MemoryRouter><QueryClientProvider client={client}><SavedSearchDialog row={{ ...row, revision }} onClose={onClose} /></QueryClientProvider></MemoryRouter></ThemeProvider>;
  const { rerender } = render(tree(1));
  fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), { target: { value: 'My sports' } });
  rerender(tree(2));
  expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('My sports');
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));
  await waitFor(() => expect(api.save).toHaveBeenCalledTimes(1));
  expect(api.save).toHaveBeenCalledWith(expect.objectContaining({ name: 'My sports' }), expect.objectContaining({ revision: 1 }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled());
  await act(async () => fail(new Error('unavailable')));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Cancel' })).toBeEnabled());
  expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('My sports');
  expect(onClose).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  const confirmation = await screen.findByRole('dialog', { name: 'Discard unsaved changes?' });
  expect(onClose).not.toHaveBeenCalled();
  fireEvent.click(within(confirmation).getByRole('button', { name: 'Discard changes' }));
  await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
});

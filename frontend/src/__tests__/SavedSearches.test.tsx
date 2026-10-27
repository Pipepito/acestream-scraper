import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
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

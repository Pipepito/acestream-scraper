import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import ImportExclusions from '../components/imports/ImportExclusions';
import { importExclusionService as service } from '../services/importExclusionService';
jest.mock('../services/importExclusionService');
const api = jest.mocked(service);
function setup(path = '/scraper?tab=exclusions') { return render(<ThemeProvider theme={createAppTheme('light')}><MemoryRouter initialEntries={[path]}><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><ImportExclusions /></QueryClientProvider></MemoryRouter></ThemeProvider>); }
beforeEach(() => { jest.resetAllMocks(); api.list.mockResolvedValue({ items: [], total: 0, policy_revision: 0 }); });
it('opens the exact linked rule independently of pagination', async () => {
  setup('/scraper?tab=exclusions#rule-487');
  expect(await screen.findByText('This exclusion no longer exists.')).toBeInTheDocument();
  expect(api.list).toHaveBeenCalledWith(0, expect.any(AbortSignal), 487);
  expect(screen.getByRole('link', { name: 'Show all rules' })).toHaveAttribute('href', '/scraper?tab=exclusions');
});
it('previews bounded matches without saving or deleting inventory', async () => {
  api.preview.mockResolvedValue({ policy_revision: 0, scanned: 10000, matched: 42, complete: false, examples: [] });
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Add exclusion' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Value' }), { target: { value: 'Sport' } });
  fireEvent.click(screen.getByRole('button', { name: 'Preview matches' }));
  expect(await screen.findByText(/At least 42 matches/)).toBeInTheDocument();
  expect(api.save).not.toHaveBeenCalled();
  expect(api.remove).not.toHaveBeenCalled();
});
it('saves a rule only after explicit Save', async () => {
  api.save.mockResolvedValue({ policy_revision: 1, rule: { id: 1, revision: 1, kind: 'name_contains', value: 'Sport', enabled: true, created_at: '', updated_at: '' } });
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Add exclusion' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Value' }), { target: { value: 'Sport' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save exclusion' }));
  await waitFor(() => expect(api.save).toHaveBeenCalledWith(expect.objectContaining({ value: 'Sport', enabled: true }), undefined));
});

import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SourceEditor from '../components/scraper/SourceEditor';
import { scraperService, type ScrapedURL } from '../services/scraperService';
import { ApiError } from '../services/apiErrors';

jest.mock('../services/scraperService');
const api = jest.mocked(scraperService);
const existing: ScrapedURL = { id: 7, name: 'Existing', url: 'http://192.168.1.20/list.m3u', url_type: 'auto', enabled: true, scrape_bare_ids: false, error_count: 0, added_at: '2026-01-01T00:00:00Z' };
function mount(props: React.ComponentProps<typeof SourceEditor>) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><SourceEditor {...props} /></QueryClientProvider>);
}
beforeEach(() => { jest.clearAllMocks(); api.getProviders.mockResolvedValue([]); });

it('retains fields and exposes the failure without closing or scraping', async () => {
  api.createURL.mockRejectedValue(new ApiError({ message: 'Source address is invalid', status: 422, kind: 'validation', canRetry: false }));
  const onSaved = jest.fn(), onClose = jest.fn();
  mount({ onSaved, onClose });
  fireEvent.change(screen.getByRole('textbox', { name: /Channel source link/ }), { target: { value: existing.url } });
  fireEvent.change(screen.getByRole('textbox', { name: 'Friendly name (optional)' }), { target: { value: 'My channels' } });
  fireEvent.click(screen.getByRole('button', { name: 'Add source' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Source address is invalid');
  expect(screen.getByRole('textbox', { name: /Channel source link/ })).toHaveValue(existing.url);
  expect(screen.getByRole('textbox', { name: 'Friendly name (optional)' })).toHaveValue('My channels');
  expect(onSaved).not.toHaveBeenCalled(); expect(onClose).not.toHaveBeenCalled(); expect(api.scrapeURL).not.toHaveBeenCalled();
});

it('guards local cancel and returns to the same draft when discard is cancelled', async () => {
  const onClose = jest.fn(); mount({ onSaved: jest.fn(), onClose });
  fireEvent.change(screen.getByRole('textbox', { name: /Channel source link/ }), { target: { value: existing.url } });
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  const confirmation = await screen.findByRole('dialog', { name: 'Discard unsaved changes?' });
  fireEvent.click(within(confirmation).getByRole('button', { name: 'Cancel' }));
  await waitFor(() => expect(screen.getByRole('textbox', { name: /Channel source link/ })).toHaveValue(existing.url));
  expect(onClose).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  fireEvent.click(within(await screen.findByRole('dialog', { name: 'Discard unsaved changes?' })).getByRole('button', { name: 'Discard changes' }));
  await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
});

it('submits once, disables fields while saving and preserves the recipe by omission during edits', async () => {
  let resolve!: (source: ScrapedURL) => void;
  api.updateURL.mockReturnValue(new Promise(done => { resolve = done; }));
  const onSaved = jest.fn(); mount({ source: existing, onSaved, onClose: jest.fn() });
  fireEvent.change(screen.getByRole('textbox', { name: 'Friendly name (optional)' }), { target: { value: 'Changed' } });
  fireEvent.submit(screen.getByRole('form', { name: 'Edit source' }));
  fireEvent.submit(screen.getByRole('form', { name: 'Edit source' }));
  await waitFor(() => expect(api.updateURL).toHaveBeenCalledTimes(1));
  expect(api.updateURL.mock.calls[0]).toEqual([7, { name: 'Changed', url: existing.url, url_type: 'auto', enabled: true, scrape_bare_ids: false }]);
  expect(screen.getByRole('textbox', { name: /Channel source link/ })).toBeDisabled();
  resolve({ ...existing, name: 'Changed' });
  await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
  expect(api.createURL).not.toHaveBeenCalled(); expect(api.scrapeURL).not.toHaveBeenCalled();
});

it('reuses an existing onboarding address without another create or update', async () => {
  const onSaved = jest.fn(); mount({ onSaved, reuseSources: [existing] });
  fireEvent.change(screen.getByRole('textbox', { name: /Channel source link/ }), { target: { value: ` ${existing.url} ` } });
  fireEvent.click(screen.getByRole('button', { name: 'Add source' }));
  await waitFor(() => expect(onSaved).toHaveBeenCalledWith(existing));
  expect(api.createURL).not.toHaveBeenCalled(); expect(api.updateURL).not.toHaveBeenCalled(); expect(api.scrapeURL).not.toHaveBeenCalled();
});

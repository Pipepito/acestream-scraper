import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import FolderMatchDialog from '../components/catalogues/FolderMatchDialog';
import { catalogueService, type FolderMatchPreview } from '../services/catalogueService';
import i18n from '../i18n';

jest.mock('../services/catalogueService');
const service = jest.mocked(catalogueService);
const initial: FolderMatchPreview = { rows: [
  { folder_id: 'news', name: 'News', path: 'News', stream_count: 2, candidate: { id: 7, name: 'News' }, current: null, status: 'match' },
  { folder_id: 'sport', name: 'Sport', path: 'Sport', stream_count: 1, candidate: null, current: null, status: 'none' },
] };

afterEach(async () => { jest.resetAllMocks(); await act(async () => { await i18n.changeLanguage('en'); }); });

it('retains reviewed targets and explicit choices through refresh, language change and failed apply', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  service.folderMatches.mockResolvedValue(initial);
  service.applyFolderMatches.mockRejectedValue(new Error('Controlled failure'));
  const close = jest.fn();
  render(<QueryClientProvider client={client}><FolderMatchDialog open catalogueId={1} entries={[]}
    onClose={close} onApplied={jest.fn()} /></QueryClientProvider>);
  const user = userEvent.setup();
  const news = await screen.findByRole('checkbox', { name: 'Assign News to News' });
  await user.click(screen.getByRole('checkbox', { name: 'Create TV channel Sport' }));
  service.folderMatches.mockResolvedValue({ rows: [{ ...initial.rows[0], candidate: { id: 99, name: 'Changed target' } }] });
  await act(async () => { await client.invalidateQueries({ queryKey: ['catalogue', 1, 'folder-matches'] }); });
  expect(news).toBeChecked();
  expect(screen.getByRole('checkbox', { name: 'Create TV channel Sport' })).toBeChecked();
  expect(screen.queryByText(/Changed target/)).not.toBeInTheDocument();
  await act(async () => { await i18n.changeLanguage('es'); });
  expect(screen.getByRole('checkbox', { name: /News/ })).toBe(news);
  await user.click(screen.getByRole('button', { name: 'Aplicar coincidencias' }));
  await waitFor(() => expect(service.applyFolderMatches).toHaveBeenCalledWith(1, {
    assignments: [{ folder_id: 'news', tv_channel_id: 7 }, { folder_id: 'sport', create: true }], reassign: false,
  }));
  expect(await screen.findByRole('alert')).toBeVisible();
  expect(screen.getByRole('checkbox', { name: /Sport/ })).toBeChecked();
  expect(close).not.toHaveBeenCalled();
  client.clear();
});

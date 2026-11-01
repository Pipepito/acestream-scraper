import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import { ApiError } from '../services/apiErrors';
import Catalogues from '../pages/Catalogues';
import { catalogueService, type CatalogueView } from '../services/catalogueService';

jest.mock('../services/catalogueService');
jest.mock('../components/player/ChannelPlayerDialog', () => function MockPlayer({ open, contentId, onClose }: { open: boolean; contentId: string; onClose: () => void }) { return open
  ? <div role="dialog" aria-label="Player">{contentId}<button onClick={onClose}>Stop watching</button></div> : null; });
const mocked = jest.mocked(catalogueService);
const fixture: CatalogueView = {
  name: 'Sample catalogue', origin: 'example.test', preview_token: 'preview-token', revision: 0,
  can_refresh: true, counts: { accepted: 2, duplicates: 0, invalid: 0, unsupported: 1, failed_fetches: 0 },
  selected_branches: ['root'], entries: [
    { id: 'root', name: 'Sample catalogue', kind: 'folder' },
    { id: 'live', parent_id: 'root', name: 'Live channels', kind: 'folder' },
    { id: 'a', parent_id: 'live', name: 'Alpha HD', kind: 'acestream', channel_id: 'a'.repeat(40), reason: 'AceStream; signal not checked', origin: 'example.test' },
    { id: 'b', parent_id: 'live', name: 'Alpha HD', kind: 'hls', channel_id: `url:${'b'.repeat(40)}`, reason: 'Compatible input; availability not verified', origin: 'media.test' },
    { id: 'web', parent_id: 'root', name: 'Website player', kind: 'unsupported', reason: 'Website/embed source needs an explicit resolver adapter' },
  ],
};
const saved: CatalogueView = { ...fixture, id: 1, preview_token: undefined, entries: fixture.entries.map((e) => ({ ...e, imported: Boolean(e.channel_id) })) };

function renderPage(path = '/catalogues', mode: 'light' | 'dark' = 'light') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<ThemeProvider theme={createAppTheme(mode)}><QueryClientProvider client={client}>
    <TestMemoryRouter initialEntries={[path]}><Catalogues /></TestMemoryRouter>
  </QueryClientProvider></ThemeProvider>);
}
beforeEach(() => {
  jest.clearAllMocks(); localStorage.clear();
  mocked.list.mockResolvedValue([]); mocked.preview.mockResolvedValue(fixture);
  mocked.save.mockResolvedValue(saved); mocked.get.mockResolvedValue(saved);
});

it.each(['light', 'dark'] as const)('reviews branches and imports through the API in %s mode', async (mode) => {
  renderPage('/catalogues', mode);
  const user = userEvent.setup();
  expect(await screen.findByText(/No catalogues yet/)).toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Add catalogue' }));
  await user.type(screen.getByRole('textbox', { name: 'Catalogue URL' }), 'https://example.test/index.w3u');
  await user.click(screen.getByRole('button', { name: 'Preview URL' }));
  expect(await screen.findByRole('heading', { name: 'Review import' })).toBeVisible();
  expect(mocked.save).not.toHaveBeenCalled();
  await user.click(screen.getByRole('checkbox', { name: 'All folders' }));
  await user.click(screen.getByRole('checkbox', { name: 'Include Live channels' }));
  await user.click(screen.getByRole('checkbox', { name: 'Import selected compatible entries as permanent live channels' }));
  await user.click(screen.getByRole('button', { name: 'Save catalogue and import' }));
  expect(await screen.findByRole('button', { name: 'Preview refresh' })).toBeVisible();
  expect(mocked.save).toHaveBeenCalledWith(expect.objectContaining({ preview_token: 'preview-token', selected_branches: ['live'], mode: 'compatible' }), expect.anything());
});

it('browses variants, favorites and recent entries without starting unsupported playback', async () => {
  renderPage('/catalogues?catalogue=1');
  const user = userEvent.setup();
  await user.click(await screen.findByRole('button', { name: /Live channels Folder/ }));
  const sources = screen.getAllByRole('button', { name: /Alpha HD/ });
  await user.click(sources[0]);
  expect(screen.getByText('Other entries with this title in the same folder')).toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Add favorite' }));
  expect(JSON.parse(localStorage.getItem('acestream.catalogue-history.v1')!).favorites).toEqual(['1:a']);
  await user.click(screen.getByRole('button', { name: 'Play source' }));
  expect(within(screen.getByRole('dialog', { name: 'Player' })).getByText('a'.repeat(40))).toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Stop watching' }));
  await user.type(screen.getByRole('textbox', { name: 'Search catalogue' }), 'Website');
  await user.click(screen.getByRole('button', { name: /Website player Unsupported/ }));
  expect(screen.queryByRole('button', { name: 'Play source' })).not.toBeInTheDocument();
  expect(screen.getByText('Showing matches across all folders.')).toBeVisible();
});

it('keeps partial refresh warnings and displays fetch errors', async () => {
  mocked.preview.mockResolvedValue({ ...saved, preview_token: 'refresh-token', partial: true, warnings: ['Maximum folder depth reached'] });
  renderPage('/catalogues?catalogue=1');
  const user = userEvent.setup();
  await user.click(await screen.findByRole('button', { name: 'Preview refresh' }));
  expect(await screen.findByText(/This is a partial catalogue/)).toBeVisible();
  expect(screen.getByText('Maximum folder depth reached')).toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Discard preview' }));
  mocked.preview.mockRejectedValue(new ApiError({ message: 'Source unavailable', status: 422, kind: 'validation', canRetry: true }));
  await user.click(screen.getByRole('button', { name: 'Preview refresh' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Source unavailable');
});

it('requires a concrete removal confirmation', async () => {
  mocked.remove.mockResolvedValue();
  renderPage('/catalogues?catalogue=1');
  const user = userEvent.setup();
  await user.click(await screen.findByRole('button', { name: 'Remove catalogue' }));
  expect(mocked.remove).not.toHaveBeenCalled();
  const dialog = screen.getByRole('dialog', { name: 'Remove catalogue?' });
  expect(within(dialog).getByText(/Imported channels and manual assignments are kept/)).toBeVisible();
  await user.click(within(dialog).getByRole('button', { name: 'Remove catalogue' }));
  expect(mocked.remove).toHaveBeenCalledWith(1, expect.anything());
});

it('saves without silently classifying unknown streams as live', async () => {
  renderPage();
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: 'Add catalogue' }));
  await user.type(screen.getByRole('textbox', { name: 'Catalogue URL' }), 'https://example.test/list');
  await user.click(screen.getByRole('button', { name: 'Preview URL' }));
  await user.click(await screen.findByRole('button', { name: 'Save catalogue' }));
  expect(mocked.save).toHaveBeenCalledWith(expect.objectContaining({ confirm_live: false }), expect.anything());
});

it('previews a catalogue broadcast through the shared event review without exposing its URL', async () => {
  mocked.previewEvent.mockResolvedValue({ token: 'event-preview', events: [], warnings: [] });
  renderPage('/catalogues?catalogue=1');
  const user = userEvent.setup();
  await user.click(await screen.findByRole('button', { name: /Live channels Folder/ }));
  await user.click(screen.getAllByRole('button', { name: /Alpha HD/ })[0]);
  await user.click(screen.getByRole('button', { name: 'Add as event' }));
  expect(screen.getByRole('textbox', { name: 'Event title' })).toHaveValue('Alpha HD');
  expect(screen.queryByRole('textbox', { name: 'Stream URL' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Preview events' }));
  expect(mocked.previewEvent).toHaveBeenCalledWith(1, expect.objectContaining({ entry_ids: ['a'], title: 'Alpha HD', starts_at: null }));
  expect(await screen.findByText(/Review the schedule, then select/)).toBeVisible();
});

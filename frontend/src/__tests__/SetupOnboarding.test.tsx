import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TestMemoryRouter } from '../testUtils/router';
import Setup from '../pages/Setup';
import EPGSourceDialog from '../components/EPGSourceDialog';
import { setupService, type SetupState } from '../services/setupService';
import { scraperService, type ScrapedURL } from '../services/scraperService';
import { epgService, type EPGSource } from '../services/epgService';
import { tvChannelService, type EPGMatchAnalysisResponse } from '../services/tvChannelService';
import { epgProviders } from '../services/epgProviders';

jest.mock('../services/setupService', () => ({ setupQueryKey: ['installation-setup'], setupService: { get: jest.fn(), save: jest.fn() } }));
jest.mock('../services/scraperService');
jest.mock('../services/epgService');
jest.mock('../services/tvChannelService');
const initial: SetupState = { version: 1, setup_complete: false, revision: 'a'.repeat(64), restart_required: false, api_protected: false, runtime: { PLAYER_MAX_SESSIONS: 7 }, options: [], unavailable: {} };
const source: ScrapedURL = { id: 1, url: 'https://example.test/list.m3u', url_type: 'auto', enabled: true, error_count: 0, added_at: '2026-01-01T00:00:00Z' };
const guide: EPGSource = { id: 2, name: epgProviders[0].name, url: epgProviders[0].url, enabled: true, error_count: 0, last_updated: '2026-01-01T00:00:00Z' };
function mount() { return render(<ThemeProvider theme={createAppTheme('light')}><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><TestMemoryRouter><Setup /></TestMemoryRouter></QueryClientProvider></ThemeProvider>); }
beforeEach(() => {
  jest.resetAllMocks();
  jest.mocked(setupService.get).mockResolvedValue(initial);
  jest.mocked(setupService.save).mockResolvedValue({ ...initial, setup_complete: true });
  jest.mocked(scraperService.getURLs).mockResolvedValue([]);
  jest.mocked(epgService.getSources).mockResolvedValue([]);
});
it('adds and imports a source, then permits skipping the guide without changing runtime settings', async () => {
  jest.mocked(scraperService.createURL).mockImplementation(async () => { jest.mocked(scraperService.getURLs).mockResolvedValue([source]); return source; });
  jest.mocked(scraperService.scrapeURL).mockResolvedValue({ url_id: 1, success: true, channels_found: 4, channels_added: 4, channels_updated: 0, duration_seconds: 1 });
  mount();
  fireEvent.change(await screen.findByRole('textbox', { name: 'Channel source link' }), { target: { value: source.url } });
  await waitFor(() => expect(screen.getByRole('button', { name: 'Add source and find channels' })).toBeEnabled());
  fireEvent.click(screen.getByRole('button', { name: 'Add source and find channels' }));
  await screen.findByText(/Found 4 channels/);
  expect(scraperService.createURL).toHaveBeenCalledWith({ url: source.url, url_type: 'auto', enabled: true });
  expect(scraperService.scrapeURL).toHaveBeenCalledWith(1);
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  expect(await screen.findByRole('button', { name: 'Use EPG dobleM' })).toBeVisible();
  expect(epgService.createSource).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Finish setup' }));
  await screen.findByRole('heading', { name: 'Setup saved' });
  expect(setupService.save).toHaveBeenCalledWith({ expected_revision: initial.revision, runtime: {}, setup_complete: true });
  expect(screen.getByRole('link', { name: 'View channels' })).toHaveAttribute('href', '/acestream-channels');
});
it('retries a failed import using the saved source instead of creating another', async () => {
  jest.mocked(scraperService.createURL).mockImplementation(async () => { jest.mocked(scraperService.getURLs).mockResolvedValue([source]); return source; });
  jest.mocked(scraperService.scrapeURL).mockRejectedValue(new Error('Source unavailable'));
  mount();
  fireEvent.change(await screen.findByRole('textbox', { name: 'Channel source link' }), { target: { value: source.url } });
  await waitFor(() => expect(screen.getByRole('button', { name: 'Add source and find channels' })).toBeEnabled());
  fireEvent.click(screen.getByRole('button', { name: 'Add source and find channels' }));
  await screen.findByText(/Could not finish adding channels/);
  fireEvent.click(await screen.findByRole('button', { name: 'Find channels' }));
  await waitFor(() => expect(scraperService.scrapeURL).toHaveBeenCalledTimes(2));
  expect(scraperService.createURL).toHaveBeenCalledTimes(1);
});
it('adds the exact dobleM feed only on request and reuses an existing guide', async () => {
  jest.mocked(epgService.createSource).mockImplementation(async () => { jest.mocked(epgService.getSources).mockResolvedValue([guide]); return guide; });
  mount();
  fireEvent.click(await screen.findByRole('button', { name: 'Continue' }));
  const useGuide = await screen.findByRole('button', { name: 'Use EPG dobleM' });
  await waitFor(() => expect(useGuide).toBeEnabled());
  fireEvent.click(useGuide);
  await screen.findByRole('button', { name: 'Find matching channels' });
  expect(epgService.createSource).toHaveBeenCalledWith({ name: 'EPG dobleM', url: 'https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiaiptv.xml', enabled: true });
  expect(tvChannelService.createFromEPGAnalysis).not.toHaveBeenCalled();
});
it('previews matches without writes and applies only explicitly reviewed rows', async () => {
  jest.mocked(epgService.getSources).mockResolvedValue([guide]);
  const row = { epg_channel_id: 9, epg_channel_name: 'Example TV', epg_channel_xml_id: 'example', epg_source_id: 2, epg_source_name: guide.name, candidate_count: 1, candidates: [{ name: 'Example TV HD', acestream_channel_id: '3', match_stage: 'name', score: 1 }], can_apply: true, is_creatable: true, review_token: 'reviewed-version' };
  jest.mocked(tvChannelService.analyzeEPGMatches).mockResolvedValue({ rows: [row], summary: { creatable_rows: 1, epg_channels_analyzed: 1, matched_acestream_channels: 1, matched_epg_channels: 1, skipped_existing_tv_channels: 0 } } satisfies EPGMatchAnalysisResponse);
  jest.mocked(tvChannelService.createFromEPGAnalysis).mockResolvedValue({ created_count: 1, associated_count: 1, skipped_count: 0, failure_count: 0, row_outcomes: [] });
  mount();
  fireEvent.click(await screen.findByRole('button', { name: 'Continue' }));
  const useGuide = await screen.findByRole('button', { name: 'Use EPG dobleM' });
  await waitFor(() => expect(useGuide).toBeEnabled()); fireEvent.click(useGuide);
  fireEvent.click(await screen.findByRole('button', { name: 'Find matching channels' }));
  const checkbox = await screen.findByRole('checkbox', { name: 'Example TV' });
  expect(checkbox).not.toBeChecked();
  expect(screen.getByRole('button', { name: 'Save selected matches (0)' })).toBeDisabled();
  expect(epgService.createSource).not.toHaveBeenCalled();
  expect(tvChannelService.createFromEPGAnalysis).not.toHaveBeenCalled();
  fireEvent.click(checkbox);
  fireEvent.click(screen.getByRole('button', { name: 'Save selected matches (1)' }));
  await waitFor(() => expect(tvChannelService.createFromEPGAnalysis).toHaveBeenCalledWith({ strictness: 'strict', source_id: 2, epg_channel_ids: [9], expected_previews: { 9: 'reviewed-version' } }));
  await screen.findByText(/Created 1 TV channels/);
});
it('offers the same preset in the normal guide dialog without submitting it', () => {
  const select = jest.fn(), submit = jest.fn();
  render(<EPGSourceDialog open isEdit={false} formData={{ name: '', url: '', enabled: true }} onChange={jest.fn()} onClose={jest.fn()} onSubmit={submit} onSelectProvider={select} />);
  fireEvent.click(screen.getByRole('button', { name: 'Use EPG dobleM' }));
  expect(select).toHaveBeenCalledWith(epgProviders[0]);
  expect(submit).not.toHaveBeenCalled();
});

it('preserves a typed source while inspecting connection settings', async () => {
  mount();
  fireEvent.change(await screen.findByRole('textbox', { name: 'Channel source link' }), { target: { value: source.url } });
  fireEvent.click(screen.getByRole('button', { name: 'Connection settings (advanced)' }));
  await screen.findByRole('dialog', { name: 'Connection settings' });
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(await screen.findByRole('textbox', { name: 'Channel source link' })).toHaveValue(source.url);
});

import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TVAutoMatchDialog from '../components/TVAutoMatchDialog';
import { tvChannelService } from '../services/tvChannelService';

jest.mock('../services/tvChannelService', () => ({ tvChannelService: { previewAutoMatch: jest.fn(), applyAutoMatch: jest.fn() } }));
const preview = jest.mocked(tvChannelService.previewAutoMatch);
const apply = jest.mocked(tvChannelService.applyAutoMatch);

function setup() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false }, queries: { retry: false } } });
  render(<QueryClientProvider client={client}><TVAutoMatchDialog onClose={jest.fn()} /></QueryClientProvider>);
}

beforeEach(() => jest.clearAllMocks());

test('groups exact stations, starts unselected and submits only selected streams', async () => {
  preview.mockResolvedValue({ tv_channels: 2, unassigned_streams: 3, ambiguous_streams: 1, unmatched_streams: 0, candidates: [
    { acestream_channel_id: 'a', acestream_name: 'DAZN 1 HD', tv_channel_id: 1, tv_channel_name: 'DAZN 1', score: .99, reason: 'Normalized name', recommended: true },
    { acestream_channel_id: 'b', acestream_name: 'DAZN F1 HD', tv_channel_id: 2, tv_channel_name: 'DAZN F1', score: .99, reason: 'Exact normalized name', recommended: true },
  ] });
  apply.mockResolvedValue({ assigned_count: 1, skipped_count: 0 });
  setup();
  expect(preview).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  const checks = await screen.findAllByRole('checkbox');
  expect(checks[0]).not.toBeChecked();
  expect(screen.getByRole('button', { name: 'Assign selected (0)' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Review streams for DAZN 1' }));
  fireEvent.click(await screen.findByRole('checkbox', { name: /DAZN 1 HD/ }));
  expect(checks[1]).not.toBeChecked();
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith({ assumed_country: null, assignments: [{ acestream_channel_id: 'a', tv_channel_id: 1 }] }, expect.anything()));
  expect(await screen.findByText(/1 streams assigned/)).toBeInTheDocument();
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
});

test('shows empty analysis and supports retry after errors', async () => {
  preview.mockRejectedValueOnce(new Error('Unable to analyze')).mockResolvedValueOnce({ tv_channels: 0, unassigned_streams: 0, ambiguous_streams: 0, unmatched_streams: 0, candidates: [] });
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/Unable to analyze/);
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  expect(await screen.findByText(/No matches found/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Assign selected (0)' })).toBeDisabled();
});

test('selects a station’s backup IDs together and allows excluding an individual ID', async () => {
  preview.mockResolvedValue({ tv_channels: 1, unassigned_streams: 2, ambiguous_streams: 0, unmatched_streams: 0, candidates: [
    { acestream_channel_id: 'f1-a', acestream_name: 'DAZN F1 HD', tv_channel_id: 1, tv_channel_name: 'DAZN F1', score: .99, reason: 'Exact normalized name', recommended: true },
    { acestream_channel_id: 'f1-b', acestream_name: 'DAZN F1 SD', tv_channel_id: 1, tv_channel_name: 'DAZN F1', score: .99, reason: 'Exact normalized name', recommended: true },
  ] });
  apply.mockResolvedValue({ assigned_count: 1, skipped_count: 0 });
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  expect(await screen.findByRole('status')).toHaveTextContent('1 TV channels with 2 matching stream IDs');
  fireEvent.click(screen.getByRole('checkbox', { name: 'DAZN F1 · 2 stream IDs' }));
  expect(screen.getByRole('button', { name: 'Assign selected (2)' })).toBeEnabled();
  fireEvent.click(screen.getByRole('button', { name: 'Review streams for DAZN F1' }));
  fireEvent.click(await screen.findByRole('checkbox', { name: /DAZN F1 SD/ }));
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith({ assumed_country: null, assignments: [{ acestream_channel_id: 'f1-a', tv_channel_id: 1 }] }, expect.anything()));
});

test('changing assumed country clears the old preview and sends the same country when applying', async () => {
  preview.mockResolvedValue({ tv_channels: 1, unassigned_streams: 1, ambiguous_streams: 0, unmatched_streams: 0, candidates: [
    { acestream_channel_id: 'es-stream', acestream_name: 'DAZN 1 HD', tv_channel_id: 1, tv_channel_name: 'DAZN 1', score: .99, reason: 'Exact normalized name; country assumed: ES', recommended: true },
  ] });
  apply.mockResolvedValue({ assigned_count: 1, skipped_count: 0 });
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  fireEvent.click(await screen.findByRole('checkbox', { name: 'DAZN 1 · 1 stream ID' }));
  expect(screen.getByRole('button', { name: 'Assign selected (1)' })).toBeEnabled();
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Assume country for unlabelled channels' }));
  fireEvent.click(await screen.findByRole('option', { name: 'Spain' }));
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Assign selected (0)' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  await waitFor(() => expect(preview).toHaveBeenLastCalledWith({ assumed_country: 'ES' }, expect.anything()));
  fireEvent.click(await screen.findByRole('checkbox', { name: 'DAZN 1 · 1 stream ID' }));
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith({ assumed_country: 'ES', assignments: [{ acestream_channel_id: 'es-stream', tv_channel_id: 1 }] }, expect.anything()));
});

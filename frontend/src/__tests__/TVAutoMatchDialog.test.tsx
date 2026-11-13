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

beforeEach(() => jest.resetAllMocks());

test('groups exact stations, starts unselected and submits only selected streams', async () => {
  preview.mockResolvedValue({ tv_channels: 2, unassigned_streams: 3, ambiguous_streams: 1, unmatched_streams: 0, candidates: [
    { acestream_channel_id: 'a', acestream_name: 'DAZN 1 HD', tv_channel_id: 1, tv_channel_name: 'DAZN 1', score: .99, reason: 'Normalized name', recommended: true },
    { acestream_channel_id: 'b', acestream_name: 'DAZN F1 HD', tv_channel_id: 2, tv_channel_name: 'DAZN F1', score: .99, reason: 'Exact normalized name', recommended: true },
  ] });
  apply.mockResolvedValue({ assigned_count: 1, skipped_count: 0 });
  setup();
  expect(preview).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  await screen.findByRole('button', { name: 'Review streams for DAZN 1' });
  const checks = screen.getAllByRole('checkbox');
  expect(checks[0]).not.toBeChecked();
  expect(screen.getByRole('button', { name: 'Assign selected (0)' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Review streams for DAZN 1' }));
  fireEvent.click(await screen.findByRole('checkbox', { name: /DAZN 1 HD/ }));
  expect(checks[2]).not.toBeChecked();
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith({ assumed_country: null, include_similar: false, assignments: [{ acestream_channel_id: 'a', tv_channel_id: 1 }] }, expect.anything()));
  expect(await screen.findByText(/1 streams assigned/)).toBeInTheDocument();
  expect(screen.getAllByRole('checkbox')).toHaveLength(1);
});

test('shows empty analysis and supports retry after errors', async () => {
  preview.mockRejectedValueOnce(new Error('Unable to analyze')).mockResolvedValueOnce({ tv_channels: 0, unassigned_streams: 0, ambiguous_streams: 0, unmatched_streams: 0, candidates: [] });
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong. Try again.');
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
  expect(await screen.findByRole('status')).toHaveTextContent('1 TV channels with 2 suggestions');
  fireEvent.click(screen.getByRole('checkbox', { name: 'DAZN F1 · 2 stream IDs' }));
  expect(screen.getByRole('button', { name: 'Assign selected (2)' })).toBeEnabled();
  fireEvent.click(screen.getByRole('button', { name: 'Review streams for DAZN F1' }));
  fireEvent.click(await screen.findByRole('checkbox', { name: /DAZN F1 SD/ }));
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith({ assumed_country: null, include_similar: false, assignments: [{ acestream_channel_id: 'f1-a', tv_channel_id: 1 }] }, expect.anything()));
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
  expect(screen.getAllByRole('checkbox')).toHaveLength(1);
  expect(screen.getByRole('button', { name: 'Assign selected (0)' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  await waitFor(() => expect(preview).toHaveBeenLastCalledWith({ assumed_country: 'ES', include_similar: false }, expect.anything()));
  fireEvent.click(await screen.findByRole('checkbox', { name: 'DAZN 1 · 1 stream ID' }));
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith({ assumed_country: 'ES', include_similar: false, assignments: [{ acestream_channel_id: 'es-stream', tv_channel_id: 1 }] }, expect.anything()));
});


test('similar suggestions need individual review and allow only one target per stream', async () => {
  preview.mockResolvedValue({ tv_channels: 2, unassigned_streams: 1, ambiguous_streams: 1, unmatched_streams: 0, candidates: [
    { acestream_channel_id: 'same', acestream_name: 'Sportz HD', tv_channel_id: 1, tv_channel_name: 'Sports', score: .9, reason: 'Similar name', recommended: false },
    { acestream_channel_id: 'same', acestream_name: 'Sportz HD', tv_channel_id: 2, tv_channel_name: 'Sport', score: .8, reason: 'Similar name', recommended: false },
  ] });
  apply.mockResolvedValue({ assigned_count: 1, skipped_count: 0 });
  setup();
  fireEvent.click(screen.getByRole('checkbox', { name: 'Include similar names for review' }));
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  const suggestions = await screen.findAllByRole('checkbox', { name: /Sportz HD/ });
  expect(screen.getByRole('button', { name: 'Select all exact matches' })).toBeDisabled();
  fireEvent.click(suggestions[0]);
  fireEvent.click(suggestions[1]);
  expect(suggestions[0]).not.toBeChecked();
  expect(suggestions[1]).toBeChecked();
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith({ assumed_country: null, include_similar: true, assignments: [{ acestream_channel_id: 'same', tv_channel_id: 2 }] }, expect.anything()));
});

test('bulk exact selection respects the search filter', async () => {
  preview.mockResolvedValue({ tv_channels: 2, unassigned_streams: 2, ambiguous_streams: 0, unmatched_streams: 0, candidates: [
    { acestream_channel_id: 'a', acestream_name: 'Sports HD', tv_channel_id: 1, tv_channel_name: 'Sports', score: .99, reason: 'Exact name', recommended: true },
    { acestream_channel_id: 'b', acestream_name: 'News HD', tv_channel_id: 2, tv_channel_name: 'News', score: .99, reason: 'Exact name', recommended: true },
  ] });
  apply.mockResolvedValue({ assigned_count: 1, skipped_count: 0 });
  setup();
  fireEvent.click(screen.getByRole('button', { name: 'Find matches' }));
  fireEvent.change(await screen.findByRole('searchbox', { name: 'Filter matches' }), { target: { value: 'Sports' } });
  fireEvent.click(screen.getByRole('button', { name: 'Select filtered exact matches' }));
  fireEvent.click(screen.getByRole('button', { name: 'Assign selected (1)' }));
  await waitFor(() => expect(apply).toHaveBeenCalledWith(expect.objectContaining({ assignments: [{ acestream_channel_id: 'a', tv_channel_id: 1 }] }), expect.anything()));
});

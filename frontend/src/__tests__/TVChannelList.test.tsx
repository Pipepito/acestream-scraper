jest.mock('../components/recordings/RecordButton', () => ({ __esModule: true, default: () => <span>Record</span> }));
jest.mock('../components/player/PlayOnMenu', () => ({ __esModule: true, default: () => <span>Send</span> }));
jest.mock('../components/epg/ScheduleView', () => ({ __esModule: true, default: () => <div>Schedule</div> }));
import React from 'react';
import { render, screen } from '@testing-library/react';
import TVChannelList from '../components/livetv/TVChannelList';
import type { TVChannel } from '../types/tvChannelTypes';

const mockResolve = jest.fn();
const mockPrograms = jest.fn();
jest.mock('../hooks/useEPG', () => ({
  useResolveEPGChannel: (...args: unknown[]) => mockResolve(...args),
  useEPGPrograms: (...args: unknown[]) => mockPrograms(...args),
}));

const channel = { id: 1, name: 'Arena TV', is_active: true, epg_source_id: 1, epg_id: 'arena', acestream_channels: [{ id: 'one', is_active: true }] } as unknown as TVChannel;
const renderList = (props: Partial<React.ComponentProps<typeof TVChannelList>> = {}) =>
  render(<TVChannelList channels={[channel]} selectedId={0} now={new Date()} onWatch={jest.fn()} {...props} />);

beforeEach(() => {
  jest.clearAllMocks();
  mockResolve.mockReturnValue({ data: undefined, isLoading: false, isError: false });
  mockPrograms.mockReturnValue({ data: undefined, isLoading: false, isError: false });
});

it('keeps per-channel guide queries off while the batched Now/Next read loads', () => {
  renderList({ nowNext: undefined });
  expect(screen.getByRole('status')).toHaveTextContent('Loading programme…');
  expect(mockResolve).toHaveBeenCalledWith(1, 'arena', expect.objectContaining({ enabled: false }));
  expect(mockPrograms).toHaveBeenCalledWith(0, expect.any(String), expect.any(String), expect.objectContaining({ enabled: false }));
});

it('renders the batched programme and the guide expander without per-channel queries once the read lands', () => {
  const row = { tv_channel_id: 1, epg_channel_id: 5, now: { title: 'Live match', start: new Date(Date.now() - 60_000).toISOString(), end: new Date(Date.now() + 60_000).toISOString() }, next: null };
  renderList({ nowNext: new Map([[1, row]]) });
  expect(screen.getByText(/Now · Live match/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'TV guide for Arena TV' })).toBeInTheDocument();
  expect(mockResolve).toHaveBeenCalledWith(1, 'arena', expect.objectContaining({ enabled: false }));
});

it('falls back to per-channel guide queries only when the batched read failed', () => {
  renderList({ nowNext: undefined, nowNextFailed: true });
  expect(mockResolve).toHaveBeenCalledWith(1, 'arena', expect.objectContaining({ enabled: true }));
});

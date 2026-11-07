jest.mock('../components/recordings/RecordButton', () => ({ __esModule: true, default: () => <span>Recordings</span> }));
import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
const mockStream = jest.fn();
const mockTV = jest.fn();
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannel: (...args: unknown[]) => mockStream(...args) }));
jest.mock('../hooks/useTVChannels', () => ({ useTVChannel: (...args: unknown[]) => mockTV(...args) }));
jest.mock('../components/player/ChannelGuide', () => ({ __esModule: true, default: () => <div>Channel schedule</div> }));
jest.mock('../components/player/PlayOnMenu', () => ({ __esModule: true, default: ({ contentId }: { contentId: string }) => <button>Remote {contentId}</button> }));
jest.mock('../components/player/StreamPlayerDialog', () => ({ __esModule: true, default: ({ contentId, details, schedule, extraActions, sources }: { contentId: string; details: React.ReactNode; schedule: React.ReactNode; extraActions: React.ReactNode; sources: React.ReactNode }) => <div><output>{contentId}</output>{sources}{details}{schedule}{extraActions}</div> }));
const channel = { id: 5, name: 'Arena TV', acestream_channels: [{ id: 'one', name: 'HD', is_online: true }, { id: 'two', name: 'Backup', is_online: false }] };
describe('channel-aware player', () => {
  beforeEach(() => { jest.clearAllMocks(); mockStream.mockReturnValue({ data: { tv_channel_id: 5 } }); mockTV.mockReturnValue({ data: channel }); });
  it('discovers an assigned channel and switches both browser and remote playback from the visible sources row', () => {
    render(<ChannelPlayerDialog open contentId="one" title="Raw stream" onClose={jest.fn()} />);
    expect(mockTV).toHaveBeenCalledWith(5);
    expect(screen.getByText('Channel schedule')).toBeInTheDocument();
    const group = screen.getByRole('group', { name: 'Sources' });
    expect(within(group).getAllByRole('button')).toHaveLength(2);
    expect(within(group).getByRole('button', { name: /Source 1: HD/ })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.queryByRole('combobox', { name: 'Stream' })).not.toBeInTheDocument();
    fireEvent.click(within(group).getByRole('button', { name: /Source 2: Backup/ }));
    expect(within(group).getByRole('button', { name: /Source 2: Backup/ })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('status')).toHaveTextContent('two');
    expect(screen.getByRole('button', { name: 'Remote two' })).toBeInTheDocument();
  });
  it('keeps HTTP streams playable without offering an engine-only remote action', () => {
    const id = 'url:' + 'a'.repeat(40);
    mockTV.mockReturnValue({ data: { ...channel, acestream_channels: [{ id, name: 'laSexta' }] } });
    render(<ChannelPlayerDialog open contentId={id} title="laSexta" onClose={jest.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent(id);
    expect(screen.queryByRole('button', { name: /Remote/ })).not.toBeInTheDocument();
  });
  it('keeps unmapped IDs playable without inventing a schedule', () => {
    mockStream.mockReturnValue({ data: {} }); mockTV.mockReturnValue({ data: undefined });
    render(<ChannelPlayerDialog open contentId="raw" title="Raw stream" onClose={jest.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent('raw');
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    expect(screen.queryByRole('group', { name: 'Sources' })).not.toBeInTheDocument();
  });
});


it('keeps the selected TV source when a status refresh changes source order', () => {
  mockStream.mockReturnValue({ data: {} });
  mockTV.mockReturnValue({ data: channel });
  const props = { open: true, tvChannelId: 5, title: 'Arena', onClose: jest.fn(), hideUnavailableSources: true };
  const view = render(<ChannelPlayerDialog {...props} contentId="one" />);
  expect(screen.queryByRole('button', { name: /Backup/ })).not.toBeInTheDocument();
  mockTV.mockReturnValue({ data: { ...channel, acestream_channels: [{ ...channel.acestream_channels[1], is_online: true }, { ...channel.acestream_channels[0], is_online: false }] } });
  view.rerender(<ChannelPlayerDialog {...props} contentId="two" />);
  expect(screen.getByRole('status')).toHaveTextContent('one');
  expect(screen.getByRole('button', { name: /HD/ })).toHaveAttribute('aria-pressed', 'true');
});

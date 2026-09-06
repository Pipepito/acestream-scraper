import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
const mockStream = jest.fn();
const mockTV = jest.fn();
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannel: (...args: unknown[]) => mockStream(...args) }));
jest.mock('../hooks/useTVChannels', () => ({ useTVChannel: (...args: unknown[]) => mockTV(...args) }));
jest.mock('../components/player/ChannelGuide', () => ({ __esModule: true, default: () => <div>Channel schedule</div> }));
jest.mock('../components/player/PlayOnMenu', () => ({ __esModule: true, default: ({ contentId }: { contentId: string }) => <button>Remote {contentId}</button> }));
jest.mock('../components/player/StreamPlayerDialog', () => ({ __esModule: true, default: ({ contentId, details, extraActions }: { contentId: string; details: React.ReactNode; extraActions: React.ReactNode }) => <div><output>{contentId}</output>{details}{extraActions}</div> }));
const channel = { id: 5, name: 'Arena TV', acestream_channels: [{ id: 'one', name: 'HD', is_online: true }, { id: 'two', name: 'Backup', is_online: false }] };
describe('channel-aware player', () => {
  beforeEach(() => { jest.clearAllMocks(); mockStream.mockReturnValue({ data: { tv_channel_id: 5 } }); mockTV.mockReturnValue({ data: channel }); });
  it('discovers an assigned channel and switches both browser and remote playback', () => {
    render(<ChannelPlayerDialog open contentId="one" title="Raw stream" onClose={jest.fn()} />);
    expect(mockTV).toHaveBeenCalledWith(5);
    expect(screen.getByText('Channel schedule')).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Stream' }));
    fireEvent.click(screen.getByRole('option', { name: /Backup/ }));
    expect(screen.getByRole('status')).toHaveTextContent('two');
    expect(screen.getByRole('button', { name: 'Remote two' })).toBeInTheDocument();
  });
  it('keeps unmapped IDs playable without inventing a schedule', () => {
    mockStream.mockReturnValue({ data: {} }); mockTV.mockReturnValue({ data: undefined });
    render(<ChannelPlayerDialog open contentId="raw" title="Raw stream" onClose={jest.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent('raw');
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });
});

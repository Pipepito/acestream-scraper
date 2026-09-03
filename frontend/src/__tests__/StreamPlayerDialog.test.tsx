import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { act, fireEvent, render, screen } from '@testing-library/react';
import StreamPlayerDialog from '../components/player/StreamPlayerDialog';
import { describePlayerError } from '../components/player/playerCopy';
import { createAppTheme } from '../theme';

const mockStart = jest.fn();
const mockStatus = jest.fn();
const mockPublicUrl = jest.fn();
const mockLeave = jest.fn();
const hlsInstances: Array<{ loadSource: jest.Mock; attachMedia: jest.Mock; destroy: jest.Mock; on: jest.Mock }> = [];

jest.mock('hls.js', () => {
  class MockHls {
    static isSupported = () => true;
    static Events = { ERROR: 'hlsError' };
    static ErrorDetails = { BUFFER_INCOMPATIBLE_CODECS_ERROR: 'bufferIncompatibleCodecsError' };
    loadSource = jest.fn();
    attachMedia = jest.fn();
    destroy = jest.fn();
    on = jest.fn();
    constructor() { hlsInstances.push(this); }
  }
  return { __esModule: true, default: MockHls };
});
jest.mock('../hooks/usePlayer', () => ({
  useStartPlayerSession: () => ({ mutate: mockStart, isPending: false }),
  usePlayerSessionStatus: (id: string | null) => mockStatus(id),
}));
jest.mock('../hooks/useSystemServices', () => ({ usePublicUrl: () => mockPublicUrl() }));
jest.mock('../services/playerService', () => ({ playerService: { leaveSession: (...args: unknown[]) => mockLeave(...args) } }));

const renderDialog = (props: Partial<React.ComponentProps<typeof StreamPlayerDialog>> = {}) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <StreamPlayerDialog open contentId={'a'.repeat(40)} title="Arena TV" onClose={jest.fn()} {...props} />
    </ThemeProvider>
  );

const readySession = {
  data: { id: 's1', state: 'ready', hls_ready: true, stats: null, codecs: {}, playlist_url: '/p', viewers: 1, error: null, error_message: '' },
};

describe('StreamPlayerDialog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    hlsInstances.length = 0;
    mockPublicUrl.mockReturnValue({ data: { url: 'http://scraper.lan:8000', source: 'setting', warnings: [] } });
    mockStart.mockImplementation((_id: string, opts: { onSuccess: (s: { id: string }) => void }) => opts.onSuccess({ id: 's1' }));
  });

  it('starts a session on open, shows starting stats, then attaches hls.js when ready', () => {
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'starting', hls_ready: false, stats: { peers: 4, speed_down: 900, speed_up: 0, status: 'prebuf' }, codecs: {}, playlist_url: '/api/v1/player/sessions/s1/index.m3u8', viewers: 1, error: null, error_message: '' } });
    const { rerender } = renderDialog();
    expect(mockStart).toHaveBeenCalledWith('a'.repeat(40), expect.any(Object));
    expect(screen.getByRole('status')).toHaveTextContent(/Starting.*4 peers/);
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'ready', hls_ready: true, stats: null, codecs: { video: 'h264', audio: 'ac3' }, playlist_url: '/api/v1/player/sessions/s1/index.m3u8', viewers: 1, error: null, error_message: '' } });
    rerender(
      <ThemeProvider theme={createAppTheme('light')}>
        <StreamPlayerDialog open contentId={'a'.repeat(40)} title="Arena TV" onClose={jest.fn()} />
      </ThemeProvider>
    );
    expect(hlsInstances).toHaveLength(1);
    expect(hlsInstances[0].loadSource).toHaveBeenCalledWith('/api/v1/player/sessions/s1/index.m3u8');
  });

  it('explains errors in plain language and offers the stream link', () => {
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'error', error: 'engine_stalled', error_message: 'no peers', hls_ready: false, stats: null, codecs: {}, playlist_url: '', viewers: 1 } });
    renderDialog();
    expect(screen.getByRole('alert')).toHaveTextContent('No one is sharing this channel right now');
    expect(screen.getByRole('button', { name: 'Copy stream link' })).toBeInTheDocument();
  });

  it('leaves the session with a keepalive DELETE on pagehide', () => {
    mockStatus.mockReturnValue(readySession);
    renderDialog();
    act(() => { window.dispatchEvent(new Event('pagehide')); });
    expect(mockLeave).toHaveBeenCalledTimes(1);
    expect(mockLeave).toHaveBeenCalledWith('s1');
  });

  it('leaves the session with a keepalive DELETE on close, and only once', () => {
    mockStatus.mockReturnValue(readySession);
    const onClose = jest.fn();
    renderDialog({ onClose });
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(mockLeave).toHaveBeenCalledTimes(1);
    expect(mockLeave).toHaveBeenCalledWith('s1');
    expect(onClose).toHaveBeenCalled();
    act(() => { window.dispatchEvent(new Event('pagehide')); });
    expect(mockLeave).toHaveBeenCalledTimes(1);
  });
});

describe('describePlayerError', () => {
  it('maps codes to copy', () => {
    expect(describePlayerError({ error: 'ffmpeg_missing', error_message: '', codecs: {} }, false)).toMatch(/can't prepare streams/);
    expect(describePlayerError({ error: null, error_message: '', codecs: { video: 'mpeg2video' } }, false)).toMatch(/MPEG-2/);
    expect(describePlayerError({ error: null, error_message: '', codecs: {} }, true)).toMatch(/video format/);
    expect(describePlayerError({ error: 'engine_refused', error_message: 'activate premium', codecs: {} }, false)).toContain('activate premium');
    expect(describePlayerError({ error: null, error_message: '', codecs: { video: 'h264' } }, false)).toBeNull();
  });
});

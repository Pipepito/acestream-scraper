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
interface MockHlsInstance {
  loadSource: jest.Mock;
  attachMedia: jest.Mock;
  destroy: jest.Mock;
  startLoad: jest.Mock;
  recoverMediaError: jest.Mock;
  on: jest.Mock;
}
const hlsInstances: MockHlsInstance[] = [];

// The real hls.js constant values, so the component's comparisons are exercised
// rather than matching `undefined === undefined`.
jest.mock('hls.js', () => {
  class MockHls {
    static isSupported = () => true;
    static Events = { ERROR: 'hlsError' };
    static ErrorTypes = { NETWORK_ERROR: 'networkError', MEDIA_ERROR: 'mediaError', OTHER_ERROR: 'otherError' };
    static ErrorDetails = {
      BUFFER_INCOMPATIBLE_CODECS_ERROR: 'bufferIncompatibleCodecsError',
      BUFFER_ADD_CODEC_ERROR: 'bufferAddCodecError',
    };
    loadSource = jest.fn();
    attachMedia = jest.fn();
    destroy = jest.fn();
    startLoad = jest.fn();
    recoverMediaError = jest.fn();
    on = jest.fn();
    constructor() { hlsInstances.push(this); }
  }
  return { __esModule: true, default: MockHls };
});
jest.mock('../hooks/usePlayer', () => ({
  useStartPlayerSession: () => ({ mutateAsync: mockStart, isPending: false }),
  usePlayerSessionStatus: (id: string | null) => mockStatus(id),
}));
jest.mock('../hooks/useSystemServices', () => ({ usePublicUrl: () => mockPublicUrl() }));
jest.mock('../services/playerService', () => ({ playerService: { leaveSession: (...args: unknown[]) => mockLeave(...args) } }));

const renderDialog = async (props: Partial<React.ComponentProps<typeof StreamPlayerDialog>> = {}) => {
  const view = render(
    <ThemeProvider theme={createAppTheme('light')}>
      <StreamPlayerDialog open contentId={'a'.repeat(40)} title="Arena TV" onClose={jest.fn()} {...props} />
    </ThemeProvider>
  );
  await act(async () => { await Promise.resolve(); });
  return view;
};

const readySession = {
  data: { id: 's1', state: 'ready', hls_ready: true, stats: null, codecs: {}, playlist_url: '/p', viewers: 1, error: null, error_message: '' },
};

describe('StreamPlayerDialog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    hlsInstances.length = 0;
    mockPublicUrl.mockReturnValue({ data: { url: 'http://scraper.lan:8000', source: 'setting', warnings: [] } });
    mockStart.mockResolvedValue({ id: 's1' });
  });

  it('keeps the inline schedule open and resizes without restarting playback', async () => {
    mockStatus.mockReturnValue(readySession);
    const Harness = () => {
      const [large, setLarge] = React.useState(false);
      return <StreamPlayerDialog inline open contentId="one" title="Arena TV" onClose={jest.fn()}
        schedule={<div>Upcoming programmes</div>} largePlayer={large} onTogglePlayerSize={() => setLarge(!large)} />;
    };
    render(<ThemeProvider theme={createAppTheme('light')}><Harness /></ThemeProvider>);
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByRole('button', { name: 'Schedule' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Upcoming programmes')).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: 'Playback options' }));
    fireEvent.click(screen.getByRole('button', { name: 'Larger player' }));
    expect(screen.getByRole('button', { name: 'Standard player' })).toHaveAttribute('aria-pressed', 'true');
    expect(mockStart).toHaveBeenCalledTimes(1);
    expect(mockLeave).not.toHaveBeenCalled();
  });

  it('starts a session on open, shows starting stats, then attaches hls.js when ready', async () => {
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'starting', hls_ready: false, stats: { peers: 4, speed_down: 900, speed_up: 0, status: 'prebuf' }, codecs: {}, playlist_url: '/api/v1/player/sessions/s1/index.m3u8', viewers: 1, error: null, error_message: '' } });
    const { rerender } = await renderDialog();
    expect(mockStart).toHaveBeenCalledWith('a'.repeat(40));
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

  it('explains errors in plain language and offers the stream link', async () => {
    mockStatus.mockReturnValue({ data: { id: 's1', state: 'error', error: 'engine_stalled', error_message: 'no peers', hls_ready: false, stats: null, codecs: {}, playlist_url: '', viewers: 1 } });
    await renderDialog();
    expect(screen.getByRole('alert')).toHaveTextContent('No one is sharing this channel right now');
    expect(screen.getByRole('button', { name: 'Copy stream link' })).toBeInTheDocument();
  });

  it('leaves the session with a keepalive DELETE on pagehide', async () => {
    mockStatus.mockReturnValue(readySession);
    await renderDialog();
    act(() => { window.dispatchEvent(new Event('pagehide')); });
    expect(mockLeave).toHaveBeenCalledTimes(1);
    expect(mockLeave).toHaveBeenCalledWith('s1');
  });

  it('leaves the session with a keepalive DELETE on close, and only once', async () => {
    mockStatus.mockReturnValue(readySession);
    const onClose = jest.fn();
    await renderDialog({ onClose });
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(mockLeave).toHaveBeenCalledTimes(1);
    expect(mockLeave).toHaveBeenCalledWith('s1');
    expect(onClose).toHaveBeenCalled();
    act(() => { window.dispatchEvent(new Event('pagehide')); });
    expect(mockLeave).toHaveBeenCalledTimes(1);
  });

  /** Drives the real starting -> ready transition, which is what attaches hls.js. */
  const renderPlaying = async () => {
    mockStatus.mockReturnValue({ data: { ...readySession.data, state: 'starting', hls_ready: false } });
    const view = await renderDialog();
    mockStatus.mockReturnValue(readySession);
    view.rerender(
      <ThemeProvider theme={createAppTheme('light')}>
        <StreamPlayerDialog open contentId={'a'.repeat(40)} title="Arena TV" onClose={jest.fn()} />
      </ThemeProvider>
    );
    expect(hlsInstances).toHaveLength(1);
    return view;
  };

  const emitHlsError = (data: Record<string, unknown>) => {
    const call = hlsInstances[0].on.mock.calls.find(([event]) => event === 'hlsError');
    const handler = call?.[1] as (event: string, payload: Record<string, unknown>) => void;
    act(() => { handler('hlsError', data); });
  };

  it('recovers from fatal hls.js network and media errors instead of freezing', async () => {
    await renderPlaying();
    emitHlsError({ fatal: false, type: 'networkError', details: 'fragLoadError' });
    expect(hlsInstances[0].startLoad).not.toHaveBeenCalled();
    emitHlsError({ fatal: true, type: 'networkError', details: 'fragLoadError' });
    expect(hlsInstances[0].startLoad).toHaveBeenCalledTimes(1);
    emitHlsError({ fatal: true, type: 'mediaError', details: 'bufferStalledError' });
    expect(hlsInstances[0].recoverMediaError).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('gives up on an unrecoverable hls.js error and says so, with a Retry', async () => {
    await renderPlaying();
    emitHlsError({ fatal: true, type: 'otherError', details: 'internalException' });
    expect(hlsInstances[0].destroy).toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/Playback stopped/);
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(mockStart).toHaveBeenCalledTimes(2);
  });

  it('explains a codec hls.js cannot buffer instead of retrying it', async () => {
    await renderPlaying();
    emitHlsError({ fatal: true, type: 'mediaError', details: 'bufferAddCodecError' });
    expect(hlsInstances[0].recoverMediaError).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/can't play this channel's video format/);
  });

  it('offers Retry when the session could never be created', async () => {
    mockStart.mockRejectedValue({ code: 'PLAYER_LIMIT_REACHED', context: { limit: 3 } });
    await renderDialog();
    expect(screen.getByRole('alert')).toHaveTextContent('Too many channels are playing at once (limit 3)');
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('offers Retry when the session was reaped, but never when ffmpeg is missing', async () => {
    mockStatus.mockReturnValue({ data: readySession.data, error: { status: 404 } });
    const { unmount } = await renderDialog();
    expect(screen.getByRole('alert')).toHaveTextContent('The stream ended.');
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    unmount();

    mockStatus.mockReturnValue({ data: { ...readySession.data, state: 'error', hls_ready: false, error: 'ffmpeg_missing' } });
    await renderDialog();
    expect(screen.getByRole('alert')).toHaveTextContent("can't prepare streams");
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument();
  });
});

describe('describePlayerError', () => {
  it('releases a session whose start finishes after the player closes', async () => {
    let resolve!: (session: { id: string }) => void;
    mockStart.mockReturnValue(new Promise((done) => { resolve = done; }));
    mockStatus.mockReturnValue({ data: undefined });
    const { unmount } = await renderDialog();
    unmount();
    await act(async () => { resolve({ id: 'late-session' }); });
    expect(mockLeave).toHaveBeenCalledWith('late-session');
  });

  it('maps codes to copy', async () => {
    expect(describePlayerError({ error: 'ffmpeg_missing', error_message: '', codecs: {} }, false)).toMatch(/can't prepare streams/);
    expect(describePlayerError({ error: null, error_message: '', codecs: { video: 'mpeg2video' } }, false)).toMatch(/MPEG-2/);
    expect(describePlayerError({ error: null, error_message: '', codecs: {} }, true)).toMatch(/video format/);
    expect(describePlayerError({ error: 'engine_refused', error_message: 'activate premium', codecs: {} }, false)).toContain('activate premium');
    expect(describePlayerError({ error: null, error_message: '', codecs: { video: 'h264' } }, false)).toBeNull();
  });
});


it('offers discovered audio languages and restarts only this viewer with the selected track', async () => {
  mockPublicUrl.mockReturnValue({ data: { url: 'http://scraper.lan:8000' } });
  mockStart.mockResolvedValue({ id: 's1' });
  mockStatus.mockReturnValue({ data: { ...readySession.data, audio_tracks: [
    { index: 0, language: 'spa', codec: 'ac3', channel_layout: 'stereo' },
    { index: 1, language: 'eng', codec: 'aac', channel_layout: 'stereo' },
  ] } });
  await renderDialog();
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Audio track' }));
  fireEvent.click(screen.getByRole('option', { name: /Track 2 · eng/ }));
  await act(async () => { await Promise.resolve(); });
  expect(mockStart).toHaveBeenLastCalledWith({ contentId: 'a'.repeat(40), audioIndex: 1 });
  expect(mockLeave).toHaveBeenCalledWith('s1');
  expect(screen.getByText(/Other viewers keep their selected track/)).toBeInTheDocument();
});

import apiClient from '../services/apiClient';
import { castService } from '../services/castService';
import { startBrowserCast, stopBrowserCast } from '../services/browserCast';

jest.mock('../services/castService', () => ({ castService: { browser: jest.fn() } }));
jest.mock('../services/apiClient', () => ({ __esModule: true, default: { delete: jest.fn() } }));

test('browser Cast declares MPEG-TS media and releases only its own receiver playback', async () => {
  const loadMedia = jest.fn().mockResolvedValue(undefined);
  const stop = jest.fn();
  let currentMedia = '';
  const session = { loadMedia, getMediaSession: () => ({ media: { contentId: currentMedia } }) };
  const context = { requestSession: jest.fn().mockResolvedValue(undefined), getCurrentSession: () => session };
  const descriptors = ['cast', 'chrome'].map(key => [key, Object.getOwnPropertyDescriptor(window, key)] as const);
  Object.defineProperty(window, 'cast', { configurable: true, value: { framework: {
    CastContext: { getInstance: () => context }, RemotePlayer: class {},
    RemotePlayerController: class { stop = stop; },
  } } });
  Object.defineProperty(window, 'chrome', { configurable: true, value: { cast: { media: {
    StreamType: { LIVE: 'LIVE' },
    MediaInfo: class { constructor(public contentId: string, public contentType: string) {} },
    LoadRequest: class { constructor(public media: object) {} },
  } } } });
  (castService.browser as jest.Mock).mockResolvedValue({ id: 'viewer', control_token: 'control',
    playlist_url: '/api/v1/viewers/viewer/media/index.m3u8?cap=media', hls_ready: true });
  (apiClient.delete as jest.Mock).mockResolvedValue({});
  try {
    await startBrowserCast({ content_id: 'a'.repeat(40) });
    expect(loadMedia).toHaveBeenCalledWith(expect.objectContaining({ media: expect.objectContaining({
      streamType: 'LIVE', hlsSegmentFormat: 'ts', hlsVideoSegmentFormat: 'mpeg2_ts',
      contentType: 'application/vnd.apple.mpegurl',
    }) }));
    currentMedia = 'https://another-app.test/video';
    await stopBrowserCast();
    expect(stop).not.toHaveBeenCalled();
    expect(apiClient.delete).toHaveBeenCalledWith('/v1/viewers/viewer', { headers: { 'X-Viewer-Token': 'control' } });
    await startBrowserCast({ content_id: 'a'.repeat(40) });
    currentMedia = loadMedia.mock.calls[1][0].media.contentId;
    await stopBrowserCast();
    expect(stop).toHaveBeenCalledTimes(1);
  } finally {
    for (const [key, descriptor] of descriptors) {
      if (descriptor) Object.defineProperty(window, key, descriptor);
      else Reflect.deleteProperty(window, key);
    }
  }
});

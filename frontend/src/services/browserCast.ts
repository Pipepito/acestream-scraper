/** Small typed boundary to Google's optional Web Sender SDK. */
import apiClient from './apiClient';
import { castService, type CastStart } from './castService';
import { ApiError } from './apiErrors';

const castError = (message: string) => new ApiError({ message, status: 409, kind: 'unknown', canRetry: false, code: 'CAST_UNAVAILABLE' });

interface CastMedia { media: { contentId: string }; }
interface CastSession { loadMedia: (request: unknown) => Promise<void>; getMediaSession: () => CastMedia | null; }
interface CastContext { setOptions: (options: object) => void; requestSession: () => Promise<void>; getCurrentSession: () => CastSession | null; }
interface CastSDK {
  framework: { CastContext: { getInstance: () => CastContext }; RemotePlayer: new () => object; RemotePlayerController: new (player: object) => { stop: () => void; playOrPause: () => void } };
}
interface ChromeCast { media: { DEFAULT_MEDIA_RECEIVER_APP_ID: string; MediaInfo: new (id: string, type: string) => { streamType?: string; hlsSegmentFormat?: string; hlsVideoSegmentFormat?: string }; LoadRequest: new (info: object) => object; StreamType: { LIVE: string } }; }
type CastWindow = Window & { cast?: CastSDK; chrome?: { cast?: ChromeCast }; __onGCastApiAvailable?: (available: boolean) => void };
let load: Promise<boolean> | undefined;
let owned: { viewer: string; control: string; url: string } | undefined;

export function loadBrowserCast(): Promise<boolean> {
  if (!window.isSecureContext) return Promise.resolve(false);
  if (load) return load;
  load = new Promise(resolve => {
    const target = window as CastWindow;
    const done = (available: boolean) => {
      window.clearTimeout(timeout);
      if (available && target.cast && target.chrome?.cast) {
        target.cast.framework.CastContext.getInstance().setOptions({ receiverApplicationId: target.chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID, autoJoinPolicy: 'origin_scoped' });
        resolve(true);
      } else resolve(false);
    };
    const timeout = window.setTimeout(() => done(false), 10000);
    target.__onGCastApiAvailable = done;
    const script = document.createElement('script');
    script.src = 'https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1';
    script.async = true; script.onerror = () => done(false);
    document.head.appendChild(script);
  });
  return load;
}

export async function startBrowserCast(payload: CastStart): Promise<void> {
  const target = window as CastWindow;
  if (!target.cast || !target.chrome?.cast) throw castError('This browser does not support Google Cast.');
  const context = target.cast.framework.CastContext.getInstance();
  // Called directly from the user's button press, before asynchronous server work.
  await context.requestSession();
  const session = context.getCurrentSession();
  if (!session) throw castError('No TV was selected.');
  const viewer = await castService.browser(payload);
  const headers = { 'X-Viewer-Token': viewer.control_token ?? '' };
  try {
    const deadline = Date.now() + 60000;
    let ready = viewer;
    while (!ready.hls_ready && Date.now() < deadline) {
      if (ready.state === 'error' || ready.state === 'stopped') throw castError('The stream could not start.');
      await new Promise(resolve => window.setTimeout(resolve, 1000));
      ready = (await apiClient.get(`/v1/viewers/${viewer.id}`, { headers })).data;
    }
    if (!ready.hls_ready) throw castError('Stream preparation timed out.');
    const url = new URL(viewer.playlist_url, window.location.href).href;
    const info = new target.chrome.cast.media.MediaInfo(url, 'application/vnd.apple.mpegurl');
    info.streamType = target.chrome.cast.media.StreamType.LIVE;
    info.hlsSegmentFormat = 'ts';
    info.hlsVideoSegmentFormat = 'mpeg2_ts';
    await session.loadMedia(new target.chrome.cast.media.LoadRequest(info));
    if (owned) await apiClient.delete(`/v1/viewers/${owned.viewer}`, { headers: { 'X-Viewer-Token': owned.control } }).catch(() => undefined);
    owned = { viewer: viewer.id, control: viewer.control_token ?? '', url };
  } catch (error) {
    await apiClient.delete(`/v1/viewers/${viewer.id}`, { headers }).catch(() => undefined);
    throw error;
  }
}

export async function stopBrowserCast(): Promise<void> {
  const target = window as CastWindow;
  const framework = target.cast?.framework;
  const session = framework?.CastContext.getInstance().getCurrentSession();
  if (owned && framework && session?.getMediaSession()?.media.contentId === owned.url) {
    new framework.RemotePlayerController(new framework.RemotePlayer()).stop();
  }
  if (owned) {
    const current = owned; owned = undefined;
    await apiClient.delete(`/v1/viewers/${current.viewer}`, { headers: { 'X-Viewer-Token': current.control } });
  }
}

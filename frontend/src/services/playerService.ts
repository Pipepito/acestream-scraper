/**
 * Web player sessions (/api/v1/player). The backend turns one AceStream
 * channel into an HLS playlist the browser can play; this module is the
 * thin transport layer for that lifecycle.
 */
import apiClient from './apiClient';
import { getApiBaseUrl } from '../config/runtime';
import { getApiToken } from './apiToken';

export type PlayerState = 'starting' | 'ready' | 'error' | 'stopped';
export type PlayerError =
  | 'engine_unavailable'
  | 'engine_refused'
  | 'engine_stalled'
  | 'ffmpeg_missing'
  | 'ffmpeg_failed';

export interface PlayerCodecs {
  video?: string | null;
  audio?: string | null;
}

export interface PlayerStats {
  status: string;
  peers: number;
  /** Engine download speed in KB/s. */
  speed_down: number;
  /** Engine upload speed in KB/s. */
  speed_up: number;
}

export interface PlayerSessionStatus {
  id: string;
  content_id: string;
  state: PlayerState;
  error: PlayerError | null;
  error_message: string;
  codecs: PlayerCodecs;
  stats: PlayerStats | null;
  viewers: number;
  playlist_url: string;
  hls_ready: boolean;
}

/** One thing the server is streaming right now: a browser session or a relay. */
export interface ActiveStream {
  kind: 'browser' | 'relay';
  id: string;
  content_id: string;
  /** Name of the acestream channel, when the server knows one with this id. */
  channel_name: string | null;
  state: 'starting' | 'ready' | 'error' | 'stopped' | 'streaming';
  viewers: number;
  peers: number | null;
  /** Relays only: who is pulling them, e.g. "tuner:192.168.1.5". */
  client_label: string | null;
  started_at: string | null;
}

export interface PlayerCapabilities {
  ffmpeg_available: boolean;
  ffmpeg_path: string | null;
  max_sessions: number;
  hls_dir: string;
}

const BASE_URL = '/v1/player';

export const playerService = {
  getCapabilities: async (): Promise<PlayerCapabilities> => {
    const { data } = await apiClient.get<PlayerCapabilities>(`${BASE_URL}/capabilities`);
    return data;
  },
  startSession: async (contentId: string): Promise<PlayerSessionStatus> => {
    const { data } = await apiClient.post<PlayerSessionStatus>(`${BASE_URL}/sessions`, { content_id: contentId });
    return data;
  },
  /** Browser sessions and tuner/remote-player relays in one list (Integrations page). */
  listActiveStreams: async (): Promise<{ streams: ActiveStream[] }> => {
    const { data } = await apiClient.get<{ streams: ActiveStream[] }>(`${BASE_URL}/streams`);
    return data;
  },
  getSession: async (id: string): Promise<PlayerSessionStatus> => {
    const { data } = await apiClient.get<PlayerSessionStatus>(`${BASE_URL}/sessions/${id}`);
    return data;
  },
  /** Fire-and-forget release; keepalive lets it complete during pagehide. sendBeacon is POST-only and cannot carry the token. */
  leaveSession: (id: string): void => {
    const token = getApiToken();
    const query = token ? `?${new URLSearchParams({ token }).toString()}` : '';
    const url = `${getApiBaseUrl({ dev: process.env.NODE_ENV === 'development' })}${BASE_URL}/sessions/${id}${query}`;
    // Best effort: the backend reaps idle sessions anyway. A rejection has to be
    // caught on the promise — try/catch would only see a synchronous throw.
    void fetch(url, { method: 'DELETE', keepalive: true }).catch(() => undefined);
  },
};

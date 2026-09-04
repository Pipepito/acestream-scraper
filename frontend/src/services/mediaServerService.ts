import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type MediaServerKind = 'jellyfin' | 'plex';
/** How channels reach Jellyfin: as an HDHomeRun tuner or as an M3U playlist. */
export type MediaServerTunerMode = 'hdhomerun' | 'm3u';
export type MediaServerSyncStatus = 'ok' | 'error' | 'never' | 'manual';

export interface MediaServer {
  id: number;
  kind: MediaServerKind;
  name: string;
  base_url: string;
  tuner_mode: MediaServerTunerMode;
  enabled: boolean;
  auto_refresh: boolean;
  has_api_key: boolean;
  connected: boolean;
  tuner_host_id: string | null;
  listing_provider_id: string | null;
  dvr_key: string | null;
  last_sync_at: string | null;
  last_sync_status: MediaServerSyncStatus;
  last_error: string | null;
  server_version: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaServerCreate {
  kind: MediaServerKind;
  name: string;
  base_url: string;
  api_key?: string | null;
  tuner_mode?: MediaServerTunerMode;
  enabled?: boolean;
  auto_refresh?: boolean;
}

/** `api_key` omitted keeps the stored secret; an empty string clears it. */
export type MediaServerUpdate = Partial<Omit<MediaServerCreate, 'kind'>>;

export interface MediaServerTestRequest {
  kind: MediaServerKind;
  base_url: string;
  api_key?: string | null;
  /** Saved server whose stored key should be reused when `api_key` is empty. */
  id?: number;
}

/** What the probe found about the key we hold: accepted, refused, or none sent. */
export type MediaServerCredentials = 'ok' | 'missing' | 'rejected';

export interface MediaServerProbe {
  reachable: boolean;
  authenticated: boolean;
  credentials: MediaServerCredentials;
  version: string | null;
  message: string;
  tuner_access: components['schemas']['TunerAccessResponse'];
}

export interface MediaServerRefreshResult {
  status: 'ok' | 'error' | 'manual';
  message: string | null;
  last_sync_at: string | null;
}

export interface MediaServerStatus {
  connected: boolean;
  channel_count: number | null;
  refresh_state: string | null;
  last_result: string | null;
  /** Plex only: the numbered set-up steps to follow in Plex Web. */
  steps: string[];
  /** Plex only: `tuner_address`, `guide_url`, `device_id` to paste into Plex. */
  paste: Record<string, string>;
  error: string | null;
}

const BASE_URL = '/v1/media-servers';

export const mediaServerService = {
  list: async (): Promise<MediaServer[]> => (await apiClient.get<MediaServer[]>(BASE_URL)).data,
  create: async (body: MediaServerCreate): Promise<MediaServer> => (await apiClient.post<MediaServer>(BASE_URL, body)).data,
  update: async (id: number, body: MediaServerUpdate): Promise<MediaServer> => (await apiClient.patch<MediaServer>(`${BASE_URL}/${id}`, body)).data,
  remove: async (id: number): Promise<void> => { await apiClient.delete(`${BASE_URL}/${id}`); },
  test: async (body: MediaServerTestRequest): Promise<MediaServerProbe> => (await apiClient.post<MediaServerProbe>(`${BASE_URL}/test`, body)).data,
  connect: async (id: number): Promise<MediaServer> => (await apiClient.post<MediaServer>(`${BASE_URL}/${id}/connect`)).data,
  refresh: async (id: number): Promise<MediaServerRefreshResult> => (await apiClient.post<MediaServerRefreshResult>(`${BASE_URL}/${id}/refresh`)).data,
  disconnect: async (id: number): Promise<MediaServer> => (await apiClient.post<MediaServer>(`${BASE_URL}/${id}/disconnect`)).data,
  status: async (id: number): Promise<MediaServerStatus> => (await apiClient.get<MediaServerStatus>(`${BASE_URL}/${id}/status`)).data,
};

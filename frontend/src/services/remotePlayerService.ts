import apiClient from './apiClient';

export type RemotePlayerKind = 'vlc' | 'kodi';
export type RemotePlayerCommand = 'pause' | 'resume' | 'stop' | 'volume';

export interface RemotePlayer {
  id: number;
  name: string;
  kind: RemotePlayerKind;
  host: string;
  port: number;
  username: string | null;
  base_url_id: number | null;
  has_password: boolean;
  created_at: string;
  updated_at: string;
}

export interface RemotePlayerCreate {
  name: string;
  kind: RemotePlayerKind;
  host: string;
  port: number;
  username?: string | null;
  password?: string | null;
  base_url_id?: number | null;
}

export interface RemotePlayerUpdate extends Partial<RemotePlayerCreate> {
  clear_base_url?: boolean;
}

export interface RemotePlayerTestRequest {
  kind: RemotePlayerKind;
  host: string;
  port: number;
  username?: string | null;
  password?: string | null;
  id?: number;
}

export interface TunerAccess {
  addresses: string[];
  allowed: boolean;
}

export interface RemotePlayerProbe {
  reachable: boolean;
  authenticated: boolean;
  version: string | null;
  message: string;
  hint: string | null;
  tuner_access: TunerAccess;
}

export interface RemotePlayerStatus {
  state: 'playing' | 'paused' | 'stopped';
  title: string | null;
  position_s: number | null;
  length_s: number | null;
  volume_pct: number | null;
  message: string | null;
}

export interface RemotePlayerPlayResult {
  url: string;
  /** Why the player probably cannot fetch `url`: localhost | docker-internal | tuner_blocked. */
  warnings?: string[];
}

export interface ScanHit {
  host: string;
  port: number;
  kind: RemotePlayerKind | 'unknown';
  hint: string;
}

export interface ScanResult {
  hosts: ScanHit[];
  scanned: number;
  duration_ms: number;
}

export interface ScanRequest {
  cidr: string;
  ports?: number[];
  timeout_ms?: number;
}

export interface ScanDefault {
  cidr: string | null;
  hint: string;
}

const BASE_URL = '/v1/remote-players';

export const remotePlayerService = {
  list: async (): Promise<RemotePlayer[]> => (await apiClient.get<RemotePlayer[]>(BASE_URL)).data,
  create: async (body: RemotePlayerCreate): Promise<RemotePlayer> => (await apiClient.post<RemotePlayer>(BASE_URL, body)).data,
  update: async (id: number, body: RemotePlayerUpdate): Promise<RemotePlayer> => (await apiClient.patch<RemotePlayer>(`${BASE_URL}/${id}`, body)).data,
  remove: async (id: number): Promise<void> => { await apiClient.delete(`${BASE_URL}/${id}`); },
  test: async (body: RemotePlayerTestRequest): Promise<RemotePlayerProbe> => (await apiClient.post<RemotePlayerProbe>(`${BASE_URL}/test`, body)).data,
  testSaved: async (id: number): Promise<RemotePlayerProbe> => (await apiClient.post<RemotePlayerProbe>(`${BASE_URL}/${id}/test`)).data,
  status: async (id: number): Promise<RemotePlayerStatus> => (await apiClient.get<RemotePlayerStatus>(`${BASE_URL}/${id}/status`)).data,
  play: async (id: number, contentId: string, title?: string): Promise<RemotePlayerPlayResult> =>
    (await apiClient.post<RemotePlayerPlayResult>(`${BASE_URL}/${id}/play`, { content_id: contentId, title })).data,
  command: async (id: number, command: RemotePlayerCommand, value?: number): Promise<void> => {
    await apiClient.post(`${BASE_URL}/${id}/command`, value === undefined ? { command } : { command, value });
  },
  scan: async (body: ScanRequest): Promise<ScanResult> => (await apiClient.post<ScanResult>(`${BASE_URL}/scan`, body)).data,
  scanDefault: async (): Promise<ScanDefault> => (await apiClient.get<ScanDefault>(`${BASE_URL}/scan/default`)).data,
};

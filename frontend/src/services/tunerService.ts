import apiClient from './apiClient';

export interface TunerSettings {
  friendly_name: string;
  tuner_count: number;
  max_channels: number;
  only_online: boolean;
}

export type TunerSettingsUpdate = Partial<TunerSettings>;

export interface TunerUrls {
  tuner: string;
  lineup: string;
  guide: string;
  playlist: string;
  epg: string;
  stream_template: string;
}

/** A channel whose own number was taken, moved to a free one. */
export interface TunerRenumbered {
  tv_channel_id: number;
  name: string;
  requested_number: number;
  assigned_number: number;
}

/** A tuner request the private-network allowlist turned away. `at` is a POSIX timestamp in seconds. */
export interface TunerDenial {
  client_ip: string;
  peer: string;
  path: string;
  at: number;
}

export interface TunerStatus {
  channel_count: number;
  renumbered: TunerRenumbered[];
  /** Channels beyond `max_channels` that the lineup left out. */
  overflow: number;
  device_id: string;
  urls: TunerUrls;
  ffmpeg_available: boolean;
  allowed_networks: string[];
  client_ip: string | null;
  peer: string | null;
  client_allowed: boolean;
  client_source: 'direct' | 'forwarded' | 'docker-gateway' | 'loopback';
  warnings: string[];
  recent_denials: TunerDenial[];
}

const BASE_URL = '/v1/tuner';

export const tunerService = {
  getSettings: async (): Promise<TunerSettings> => (await apiClient.get<TunerSettings>(`${BASE_URL}/settings`)).data,
  updateSettings: async (body: TunerSettingsUpdate): Promise<TunerSettings> =>
    (await apiClient.put<TunerSettings>(`${BASE_URL}/settings`, body)).data,
  getStatus: async (): Promise<TunerStatus> => (await apiClient.get<TunerStatus>(`${BASE_URL}/status`)).data,
};

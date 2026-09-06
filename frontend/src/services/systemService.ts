import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type ServiceState = 'running' | 'unhealthy' | 'stopped' | 'disabled' | 'external' | 'not-installed';

export interface ServiceStatus {
  name: string;
  label: string;
  description: string;
  state: ServiceState;
  installed: boolean;
  enabled: boolean;
  managed: boolean;
  stopped_by_user?: boolean;
  running: boolean;
  endpoint: string | null;
  open_streams?: components['schemas']['ServiceStatus']['open_streams'];
  stream_count_scope?: components['schemas']['ServiceStatus']['stream_count_scope'];
  version: string | null;
  distribution: string | null;
  distribution_url: string | null;
  message: string;
  pid: number | null;
  uptime_seconds: number | null;
}

export interface ServicesStatusResponse {
  services: ServiceStatus[];
  supervised: boolean;
  checked_at: string;
}

export interface ServiceRestartResponse {
  name: string;
  success: boolean;
  message: string;
}

export type PublicUrlSource = 'setting' | 'forwarded' | 'request';
export type PublicUrlWarning = 'localhost' | 'docker-internal' | 'unset' | 'proxied';

export interface PublicUrlResponse {
  url: string;
  source: PublicUrlSource;
  warnings: PublicUrlWarning[];
}

const BASE_URL = '/v1/system';

export const systemService = {
  getServices: async (): Promise<ServicesStatusResponse> => {
    const { data } = await apiClient.get<ServicesStatusResponse>(`${BASE_URL}/services`);
    return data;
  },
  restartService: async (name: string): Promise<ServiceRestartResponse> => {
    const { data } = await apiClient.post<ServiceRestartResponse>(`${BASE_URL}/services/${name}/restart`);
    return data;
  },
  controlEngine: async (action: 'start' | 'stop'): Promise<ServiceRestartResponse> => {
    const { data } = await apiClient.post<ServiceRestartResponse>(`${BASE_URL}/services/acestream/${action}`);
    return data;
  },
  /** Origin that tuners, players and copied links must use to reach this server. */
  getPublicUrl: async (): Promise<PublicUrlResponse> => {
    const { data } = await apiClient.get<PublicUrlResponse>(`${BASE_URL}/public-url`);
    return data;
  },
};

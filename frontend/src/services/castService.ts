import apiClient from './apiClient';
import type { components } from '../types/api-generated';
export type CastStatus = components['schemas']['CastStatus'];
export type CastSettings = components['schemas']['CastSettings'];
export type CastStart = components['schemas']['CastStart'];
export const castService = {
  settings: async (): Promise<CastSettings> => (await apiClient.get('/v1/cast/settings')).data,
  saveSettings: async (data: CastSettings): Promise<CastSettings> => (await apiClient.put('/v1/cast/settings', data)).data,
  trustHome: async (): Promise<CastSettings> => (await apiClient.post('/v1/cast/home-connection')).data,
  discover: async (): Promise<components['schemas']['CastDevice'][]> => (await apiClient.post('/v1/cast/discover')).data,
  capabilities: async (): Promise<components['schemas']['CastCapabilities']> => (await apiClient.get('/v1/cast/capabilities')).data,
  devices: async (): Promise<components['schemas']['CastDevice'][]> => (await apiClient.get('/v1/cast/devices')).data,
  sessions: async (): Promise<CastStatus[]> => (await apiClient.get('/v1/cast/sessions')).data,
  start: async (data: CastStart): Promise<CastStatus> => (await apiClient.post('/v1/cast/sessions', data)).data,
  command: async (id: string, action: 'play' | 'pause' | 'stop' | 'volume', volume?: number) => apiClient.post(`/v1/cast/sessions/${id}/commands`, { action, volume }),
  browser: async (data: CastStart): Promise<components['schemas']['ViewerStatus']> => (await apiClient.post('/v1/cast/browser', data)).data,
};

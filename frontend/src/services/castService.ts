import apiClient from './apiClient';
import type { components } from '../types/api-generated';
export type CastStatus = components['schemas']['CastStatus'];
export type CastStart = components['schemas']['CastStart'];
export const castService = {
  capabilities: async (): Promise<components['schemas']['CastCapabilities']> => (await apiClient.get('/v1/cast/capabilities')).data,
  devices: async (): Promise<components['schemas']['CastDevice'][]> => (await apiClient.get('/v1/cast/devices')).data,
  sessions: async (): Promise<CastStatus[]> => (await apiClient.get('/v1/cast/sessions')).data,
  start: async (data: CastStart): Promise<CastStatus> => (await apiClient.post('/v1/cast/sessions', data)).data,
  command: async (id: string, action: 'play' | 'pause' | 'stop' | 'volume', volume?: number) => apiClient.post(`/v1/cast/sessions/${id}/commands`, { action, volume }),
  browser: async (data: CastStart): Promise<components['schemas']['ViewerStatus']> => (await apiClient.post('/v1/cast/browser', data)).data,
};

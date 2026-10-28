import apiClient from './apiClient';
import { getApiToken } from './apiToken';
import type { components } from '../types/api-generated';
export type Recording = components['schemas']['RecordingView'];
export type RecordingFile = components['schemas']['RecordingFile'];
export type RecordingCreate = components['schemas']['RecordingCreate'];
export type RecordingSettings = components['schemas']['RecordingSettings'];
export type RecordingEdit = components['schemas']['RecordingEdit'];
export type RecordingCapabilities = components['schemas']['RecordingCapabilities'];
const base = '/v1/recordings';
export const recordingService = {
  currentProgramme: async (tv_channel_id: number) => (await apiClient.get<components['schemas']['ProgrammeSelection'] | null>(`${base}/current-programme`, { params: { tv_channel_id } })).data,
  upcoming: async () => (await apiClient.get<components['schemas']['RecordingList']>(`${base}/upcoming`)).data,
  openPlayback: async (id: string, file_id: string) => (await apiClient.post<components['schemas']['RecordingPlaybackView']>(`${base}/${id}/playback-sessions`, { file_id })).data,
  playback: async (id: string, sid: string) => (await apiClient.get<components['schemas']['RecordingPlaybackView']>(`${base}/${id}/playback-sessions/${sid}`)).data,
  closePlayback: async (id: string, sid: string) => { await apiClient.delete(`${base}/${id}/playback-sessions/${sid}`); },
  list: async (state?: string, offset = 0, search = '') => (await apiClient.get<components['schemas']['RecordingList']>(base, { params: { state: state || undefined, offset, limit: 50, search } })).data,
  get: async (id: string) => (await apiClient.get<Recording>(`${base}/${id}`)).data,
  capabilities: async () => (await apiClient.get<RecordingCapabilities>(`${base}/capabilities`)).data,
  create: async (data: RecordingCreate) => (await apiClient.post<Recording>(base, data)).data,
  edit: async (id: string, data: RecordingEdit) => (await apiClient.patch<Recording>(`${base}/${id}`, data)).data,
  stop: async (id: string) => (await apiClient.post<Recording>(`${base}/${id}/stop`)).data,
  cancel: async (id: string) => (await apiClient.post<Recording>(`${base}/${id}/cancel`)).data,
  delete: async (id: string) => (await apiClient.delete<Recording>(`${base}/${id}`)).data,
  convert: async (id: string, file_id: string, profile: 'remux' | 'aac') => (await apiClient.post<RecordingFile>(`${base}/${id}/conversions`, { file_id, profile })).data,
  settings: async () => (await apiClient.get<RecordingSettings>('/v1/config/recordings')).data,
  configure: async (data: RecordingSettings) => (await apiClient.put<RecordingSettings>('/v1/config/recordings', data)).data,
};
export function recordingFileUrl(id: string, fid: string, download = false): string {
  const params = new URLSearchParams();
  if (download) params.set('download', 'true');
  const token = getApiToken();
  if (token) params.set('token', token);
  return `${apiClient.defaults.baseURL}${base}/${encodeURIComponent(id)}/files/${encodeURIComponent(fid)}?${params}`;
}

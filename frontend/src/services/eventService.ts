import apiClient from './apiClient';
import type { components } from '../types/api-generated';
export type SportingEvent = components['schemas']['EventView'];
export type EventFields = components['schemas']['EventFields'];
export type EventPreview = components['schemas']['EventPreview'];
export type EventImport = components['schemas']['EventImport'];
export type EventSource = components['schemas']['EventSourceView'];
export type EventRetention = components['schemas']['EventRetention'];
export type EventSourcePreviewRequest = components['schemas']['EventSourcePreviewRequest'];
export type EventUpdate = components['schemas']['EventUpdate'];
export interface EventFilters {
  search: string; sport: string; competition: string; source: string; zone: string;
  day?: string; upcoming: boolean; followed: boolean; archived: boolean; offset: number;
}
export const eventService = {
  list: async (params: EventFilters): Promise<components['schemas']['EventList']> =>
    (await apiClient.get('/v1/events', { params })).data,
  get: async (id: string): Promise<SportingEvent> => (await apiClient.get(`/v1/events/${id}`)).data,
  preview: async (input: EventImport): Promise<EventPreview> => (await apiClient.post('/v1/events/preview', input)).data,
  apply: async (token: string, selected_ids: string[], refresh_source = false): Promise<SportingEvent[]> =>
    (await apiClient.post('/v1/events/apply', { token, selected_ids, refresh_source })).data,
  sources: async (): Promise<EventSource[]> => (await apiClient.get('/v1/events/sources')).data,
  previewSource: async (input: EventSourcePreviewRequest): Promise<EventPreview> => (await apiClient.post('/v1/events/sources/preview', input)).data,
  updateSource: async (id: string, revision: number, enabled: boolean): Promise<EventSource> =>
    (await apiClient.patch(`/v1/events/sources/${id}`, { revision, enabled })).data,
  refreshSources: async (): Promise<components['schemas']['EventRefreshQueued']> => (await apiClient.post('/v1/events/sources/refresh')).data,
  retention: async (): Promise<EventRetention> => (await apiClient.get('/v1/events/retention')).data,
  saveRetention: async (input: EventRetention): Promise<EventRetention> => (await apiClient.patch('/v1/events/retention', input)).data,
  artwork: async (id: string, signal?: AbortSignal): Promise<Blob> => (await apiClient.get(`/v1/events/${id}/artwork`, { responseType: 'blob', signal })).data,
  mapBroadcast: async (id: string, revision: number, broadcast_id: string, channel_id: string | null): Promise<SportingEvent> =>
    (await apiClient.patch(`/v1/events/${id}/broadcast`, { revision, broadcast_id, channel_id })).data,
  update: async (id: string, input: EventUpdate): Promise<SportingEvent> =>
    (await apiClient.patch(`/v1/events/${id}`, input)).data,
};

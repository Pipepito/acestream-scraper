import apiClient from './apiClient';
import type { components } from '../types/api-generated';
export type EventOverlayRequest = components['schemas']['EventOverlayRequest'];
export type EventOverlayPreview = components['schemas']['EventOverlayPreview'];
export type EventOverlayView = components['schemas']['EventOverlayView'];
export type EventInterests = components['schemas']['EventInterests'];
export type EventProviderOptions = components['schemas']['EventProviderOptions'];
export type EventChannelTarget = components['schemas']['EventChannelTarget'];
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
  interests?: string; window_days?: number; selection?: 'agenda' | 'dashboard'; limit?: number;
  day?: string; upcoming: boolean; followed: boolean; archived: boolean; offset: number;
}
export const eventService = {
  overlays: async (id: string): Promise<EventOverlayView[]> => (await apiClient.get(`/v1/events/${id}/guide-overlays`)).data,
  previewOverlay: async (id: string, input: EventOverlayRequest): Promise<EventOverlayPreview> =>
    (await apiClient.post(`/v1/events/${id}/guide-overlays/preview`, input)).data,
  applyOverlay: async (id: string, input: EventOverlayRequest, expected_fingerprint: string): Promise<EventOverlayView[]> =>
    (await apiClient.post(`/v1/events/${id}/guide-overlays`, { ...input, expected_fingerprint })).data,
  removeOverlay: async (id: string, revision: number, broadcast_id: string): Promise<void> => {
    await apiClient.delete(`/v1/events/${id}/guide-overlays`, { params: { revision, broadcast_id } });
  },
  list: async (params: EventFilters): Promise<components['schemas']['EventList']> =>
    (await apiClient.get('/v1/events', { params })).data,
  get: async (id: string): Promise<SportingEvent> => (await apiClient.get(`/v1/events/${id}`)).data,
  preview: async (input: EventImport): Promise<EventPreview> => (await apiClient.post('/v1/events/preview', input)).data,
  apply: async (token: string, selected_ids: string[], refresh_source = false): Promise<SportingEvent[]> =>
    (await apiClient.post('/v1/events/apply', { token, selected_ids, refresh_source })).data,
  providers: async (): Promise<components['schemas']['EventProviderCatalog']> => (await apiClient.get('/v1/events/providers')).data,
  interests: async (): Promise<EventInterests> => (await apiClient.get('/v1/events/interests')).data,
  broadcastTargets: async (search: string): Promise<EventChannelTarget[]> => (await apiClient.get('/v1/events/broadcast-targets', { params: { search } })).data,
  mapBroadcastTarget: async (id: string, revision: number, broadcast_id: string, target: EventChannelTarget): Promise<SportingEvent> =>
    (await apiClient.patch(`/v1/events/${id}/broadcast`, { revision, broadcast_id, target_kind: target.kind, target_id: target.id })).data,
  sources: async (): Promise<EventSource[]> => (await apiClient.get('/v1/events/sources')).data,
  previewSource: async (input: EventSourcePreviewRequest): Promise<EventPreview> => (await apiClient.post('/v1/events/sources/preview', input, { timeout: ((input.timeout_seconds ?? 300) + 30) * 1000 })).data,
  updateSource: async (id: string, revision: number, enabled: boolean): Promise<EventSource> =>
    (await apiClient.patch(`/v1/events/sources/${id}`, { revision, enabled })).data,
  deleteSource: async (id: string, revision: number): Promise<void> => { await apiClient.delete(`/v1/events/sources/${id}`, { params: { revision } }); },
  refreshSources: async (): Promise<components['schemas']['EventRefreshQueued']> => (await apiClient.post('/v1/events/sources/refresh')).data,
  retention: async (): Promise<EventRetention> => (await apiClient.get('/v1/events/retention')).data,
  saveRetention: async (input: EventRetention): Promise<EventRetention> => (await apiClient.patch('/v1/events/retention', input)).data,
  artwork: async (id: string, signal?: AbortSignal): Promise<Blob> => (await apiClient.get(`/v1/events/${id}/artwork`, { responseType: 'blob', signal })).data,
  mapBroadcast: async (id: string, revision: number, broadcast_id: string, channel_id: string | null): Promise<SportingEvent> =>
    (await apiClient.patch(`/v1/events/${id}/broadcast`, { revision, broadcast_id, channel_id })).data,
  update: async (id: string, input: EventUpdate): Promise<SportingEvent> =>
    (await apiClient.patch(`/v1/events/${id}`, input)).data,
};

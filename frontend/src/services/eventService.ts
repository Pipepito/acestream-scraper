import apiClient from './apiClient';
import type { components } from '../types/api-generated';
export type SportingEvent = components['schemas']['EventView'];
export type EventFields = components['schemas']['EventFields'];
export type EventPreview = components['schemas']['EventPreview'];
export type EventImport = components['schemas']['EventImport'];
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
  apply: async (token: string, selected_ids: string[]): Promise<SportingEvent[]> =>
    (await apiClient.post('/v1/events/apply', { token, selected_ids })).data,
  update: async (id: string, input: EventUpdate): Promise<SportingEvent> =>
    (await apiClient.patch(`/v1/events/${id}`, input)).data,
};

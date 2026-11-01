import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type CatalogueView = components['schemas']['CatalogueView'];
export type CatalogueEntry = components['schemas']['CatalogueEntry'];
export type CatalogueSummary = components['schemas']['CatalogueSummary'];
export type CataloguePreviewRequest = components['schemas']['CataloguePreviewRequest'];
export type CatalogueSaveRequest = components['schemas']['CatalogueSaveRequest'];

export const catalogueService = {
  list: async (): Promise<CatalogueSummary[]> => (await apiClient.get('/v1/catalogues')).data,
  get: async (id: number): Promise<CatalogueView> => (await apiClient.get(`/v1/catalogues/${id}`)).data,
  preview: async (request: CataloguePreviewRequest): Promise<CatalogueView> =>
    (await apiClient.post('/v1/catalogues/preview', request, { timeout: 60000 })).data,
  save: async (request: CatalogueSaveRequest): Promise<CatalogueView> =>
    (await apiClient.post('/v1/catalogues', request)).data,
  previewEvent: async (id: number, request: components['schemas']['CatalogueEventPreviewRequest']): Promise<components['schemas']['EventPreview']> =>
    (await apiClient.post(`/v1/catalogues/${id}/events/preview`, request)).data,
  remove: async (id: number): Promise<void> => { await apiClient.delete(`/v1/catalogues/${id}`); },
};

import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type CatalogueView = components['schemas']['CatalogueView'];
export type CatalogueEntry = components['schemas']['CatalogueEntry'];
export type CatalogueSummary = components['schemas']['CatalogueSummary'];
export type CataloguePreviewRequest = components['schemas']['CataloguePreviewRequest'];
export type CatalogueSaveRequest = components['schemas']['CatalogueSaveRequest'];
export type FolderAssignRequest = components['schemas']['FolderAssignRequest'];
export type FolderAssignResult = components['schemas']['FolderAssignResult'];
export type FolderMatchPreview = components['schemas']['FolderMatchPreview'];
export type FolderMatchRow = components['schemas']['FolderMatchRow'];
export type FolderMatchApplyRequest = components['schemas']['FolderMatchApplyRequest'];
export type FolderMatchApplyResult = components['schemas']['FolderMatchApplyResult'];

export const catalogueService = {
  assignFolder: async (id: number, folderId: string, request: FolderAssignRequest): Promise<FolderAssignResult> =>
    (await apiClient.post(`/v1/catalogues/${id}/folders/${encodeURIComponent(folderId)}/tv-channel`, request)).data,
  folderMatches: async (id: number): Promise<FolderMatchPreview> => (await apiClient.post(`/v1/catalogues/${id}/folder-matches/preview`)).data,
  applyFolderMatches: async (id: number, request: FolderMatchApplyRequest): Promise<FolderMatchApplyResult> =>
    (await apiClient.post(`/v1/catalogues/${id}/folder-matches/apply`, request)).data,
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

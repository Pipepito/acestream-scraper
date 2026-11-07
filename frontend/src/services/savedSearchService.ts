import apiClient from './apiClient';
import type { components } from '../types/api-generated';
export type SavedSearchInput = components['schemas']['SavedSearchInput'];
export type SavedSearch = components['schemas']['SavedSearchView'];
export type SavedSearchResult = components['schemas']['SavedSearchResult'];
export type SavedSearchPreview = components['schemas']['SavedSearchPreview'];
const root = '/v1/saved-searches';
export const savedSearchService = {
  list: async (offset = 0, signal?: AbortSignal) => (await apiClient.get<components['schemas']['SavedSearchList']>(root, { params: { offset }, signal })).data,
  get: async (id: number, signal?: AbortSignal) => (await apiClient.get<SavedSearch>(`${root}/${id}`, { signal })).data,
  save: async (data: SavedSearchInput, row?: SavedSearch) => row
    ? (await apiClient.patch<SavedSearch>(`${root}/${row.id}`, { ...data, expected_revision: row.revision })).data
    : (await apiClient.post<SavedSearch>(root, data)).data,
  remove: async (row: SavedSearch) => apiClient.delete(`${root}/${row.id}`, { params: { expected_revision: row.revision } }),
  preview: async (row: SavedSearch) => (await apiClient.post<SavedSearchPreview>(`${root}/preview`, { saved_search_id: row.id, expected_revision: row.revision }, { timeout: 135000 })).data,
  run: async (row: SavedSearch, previewToken?: string) => (await apiClient.post<SavedSearch>(`${root}/${row.id}/run`, { expected_revision: row.revision, preview_token: previewToken })).data,
};

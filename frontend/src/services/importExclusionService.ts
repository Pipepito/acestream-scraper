import apiClient from './apiClient';
import type { components } from '../types/api-generated';
export type ExclusionInput = components['schemas']['ExclusionInput'];
export type ExclusionRule = components['schemas']['ExclusionRule'];
export type ExclusionPreview = components['schemas']['ExclusionPreview'];
const root = '/v1/import-exclusions';
export const importExclusionService = {
  list: async (offset = 0, signal?: AbortSignal, ruleId?: number) => (await apiClient.get<components['schemas']['ExclusionList']>(root, { params: { offset, rule_id: ruleId }, signal })).data,
  save: async (data: ExclusionInput, row?: ExclusionRule) => row
    ? (await apiClient.patch<components['schemas']['ExclusionWrite']>(`${root}/${row.id}`, { ...data, expected_revision: row.revision })).data
    : (await apiClient.post<components['schemas']['ExclusionWrite']>(root, data)).data,
  remove: async (row: ExclusionRule) => apiClient.delete(`${root}/${row.id}`, { params: { expected_revision: row.revision } }),
  preview: async (data: ExclusionInput) => (await apiClient.post<ExclusionPreview>(`${root}/preview`, data)).data,
};

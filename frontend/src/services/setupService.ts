import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type SetupState = components['schemas']['SetupState'];
export type SetupUpdate = components['schemas']['SetupUpdate'];
export type RuntimeOption = components['schemas']['RuntimeOption'];
export const setupQueryKey = ['installation-setup'];
export const setupService = {
  get: async (): Promise<SetupState> => (await apiClient.get<SetupState>('/v1/setup')).data,
  save: async (request: SetupUpdate): Promise<SetupState> => (await apiClient.put<SetupState>('/v1/setup', request)).data,
};

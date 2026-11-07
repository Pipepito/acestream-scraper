import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type GuideMatchingConfig = components['schemas']['EPGMatchingConfig'];
export type GuideMatchingRun = components['schemas']['EPGMatchingRun'];
export type GuideCoverage = components['schemas']['PlaylistGuideCoverage'];

export const guideSetupService = {
  coverage: async (): Promise<GuideCoverage> => (await apiClient.get<GuideCoverage>('/v1/playlists/guide-coverage')).data,
  config: async (): Promise<GuideMatchingConfig> => (await apiClient.get<GuideMatchingConfig>('/v1/config/epg-matching')).data,
  saveConfig: async (config: GuideMatchingConfig): Promise<GuideMatchingConfig> => (await apiClient.put<GuideMatchingConfig>('/v1/config/epg-matching', config)).data,
  lastRun: async (): Promise<GuideMatchingRun> => (await apiClient.get<GuideMatchingRun>('/v1/config/epg-matching/last-run')).data,
};

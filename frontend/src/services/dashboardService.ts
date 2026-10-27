// Scheduler status used by the TV and system dashboards
import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type BackgroundTaskStatus = components['schemas']['BackgroundTaskStatus'];

export const getBackgroundTaskStatus = () =>
  apiClient.get<BackgroundTaskStatus[]>('/v1/background-tasks/status');

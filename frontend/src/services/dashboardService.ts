// Scheduler status used by the Overview page
import apiClient from './apiClient';

export interface BackgroundTaskStatus {
  task_name: string;
  last_run: string | null;
  next_run: string | null;
  status: string;
  last_error: string | null;
  last_result: unknown;
  progress: { processed?: number; total?: number; percent?: number } | null;
}

export const getBackgroundTaskStatus = () =>
  apiClient.get<BackgroundTaskStatus[]>('/v1/background-tasks/status');

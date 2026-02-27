// Dashboard API service for activity, background tasks, streams, warp, and dashboard config
import apiClient from './apiClient';

export const getRecentActivity = (params: { days?: number; type?: string; page?: number; page_size?: number }) =>
  apiClient.get('/v1/activity/recent', { params });

export const getBackgroundTaskStatus = () =>
  apiClient.get('/v1/background-tasks/status');

export const getActiveStreams = () =>
  apiClient.get('/v1/streams/active');

export const getWarpStatus = () =>
  apiClient.get('/v1/warp/status');

export const getDashboardConfig = () =>
  apiClient.get('/v1/config/dashboard');

export const updateDashboardConfig = (data: { retention_days?: number; auto_refresh_interval?: number }) =>
  apiClient.put('/v1/config/dashboard', data);

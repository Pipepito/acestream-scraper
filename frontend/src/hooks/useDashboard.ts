// React hooks for dashboard activity, status, streams, warp, and config
import { useQuery, useMutation, useQueryClient } from 'react-query';
import * as dashboardService from '../services/dashboardService';

export function useRecentActivity(params: { days?: number; type?: string; page?: number; page_size?: number }) {
  return useQuery(['dashboard-activity', params], () => dashboardService.getRecentActivity(params).then(r => r.data));
}

export function useBackgroundTaskStatus() {
  return useQuery('dashboard-background-tasks', () => dashboardService.getBackgroundTaskStatus().then(r => r.data), {
    refetchInterval: false,
  });
}

export function useActiveStreams() {
  return useQuery('dashboard-active-streams', () => dashboardService.getActiveStreams().then(r => r.data), {
    refetchInterval: false,
  });
}

export function useWarpStatus() {
  return useQuery('dashboard-warp-status', () => dashboardService.getWarpStatus().then(r => r.data), {
    refetchInterval: false,
  });
}

export function useDashboardConfig() {
  return useQuery('dashboard-config', () => dashboardService.getDashboardConfig().then(r => r.data));
}

export function useUpdateDashboardConfig() {
  const queryClient = useQueryClient();
  return useMutation(dashboardService.updateDashboardConfig, {
    onSuccess: () => {
      queryClient.invalidateQueries('dashboard-config');
    },
  });
}

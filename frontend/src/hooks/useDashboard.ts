// React hooks for dashboard activity, status, streams, warp, and config
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as dashboardService from '../services/dashboardService';

export function useRecentActivity(params: { days?: number; type?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['dashboard-activity', params],
    queryFn: () => dashboardService.getRecentActivity(params).then(r => r.data),
  });
}

export function useBackgroundTaskStatus() {
  return useQuery({
    queryKey: ['dashboard-background-tasks'],
    queryFn: () => dashboardService.getBackgroundTaskStatus().then(r => r.data),
    refetchInterval: false,
  });
}

export function useActiveStreams() {
  return useQuery({
    queryKey: ['dashboard-active-streams'],
    queryFn: () => dashboardService.getActiveStreams().then(r => r.data),
    refetchInterval: false,
  });
}

export function useWarpStatus() {
  return useQuery({
    queryKey: ['dashboard-warp-status'],
    queryFn: () => dashboardService.getWarpStatus().then(r => r.data),
    refetchInterval: false,
  });
}

export function useDashboardConfig() {
  return useQuery({
    queryKey: ['dashboard-config'],
    queryFn: () => dashboardService.getDashboardConfig().then(r => r.data),
  });
}

export function useUpdateDashboardConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dashboardService.updateDashboardConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-config'] });
    },
  });
}

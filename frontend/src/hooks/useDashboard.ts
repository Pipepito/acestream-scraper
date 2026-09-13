// React hooks for scheduler status
import { useQuery } from '@tanstack/react-query';
import * as dashboardService from '../services/dashboardService';

export function useBackgroundTaskStatus(refetchInterval: number | false = false) {
  return useQuery({
    queryKey: ['dashboard-background-tasks'],
    queryFn: () => dashboardService.getBackgroundTaskStatus().then((r) => r.data),
    refetchInterval,
  });
}

import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from '@tanstack/react-query';
import { systemService, type ServicesStatusResponse } from '../services/systemService';

export const SYSTEM_SERVICES_QUERY_KEY = ['system', 'services'] as const;

type QueryOpts = Omit<UseQueryOptions<ServicesStatusResponse>, 'queryKey' | 'queryFn'>;

/** Status of the sidecar services (engine, Acexy, IPFS, ZeroNet, WARP). */
export const useSystemServices = (options: QueryOpts = {}) =>
  useQuery<ServicesStatusResponse>({
    queryKey: SYSTEM_SERVICES_QUERY_KEY,
    queryFn: systemService.getServices,
    ...options,
  });

/** Ask the container supervisor to restart one service. */
export const useRestartService = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => systemService.restartService(name),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SYSTEM_SERVICES_QUERY_KEY });
    },
  });
};

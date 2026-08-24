import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { configService, HealthResponse, Stats, StatusResponse } from '../services/configService';

type QueryOpts<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

/**
 * Hook for getting the base URL setting
 */
export const useBaseUrl = () => {
  return useQuery({ queryKey: ['baseUrl'], queryFn: configService.getBaseUrl });
};

/**
 * Hook for updating the base URL setting
 */
export const useUpdateBaseUrl = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (baseUrl: string) => configService.updateBaseUrl(baseUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['baseUrl'] });
      queryClient.invalidateQueries({ queryKey: ['allSettings'] });
    },
  });
};

/**
 * Hook for getting the Acestream Engine URL setting
 */
export const useAceEngineUrl = () => {
  return useQuery({ queryKey: ['aceEngineUrl'], queryFn: configService.getAceEngineUrl });
};

/**
 * Hook for updating the Acestream Engine URL setting
 */
export const useUpdateAceEngineUrl = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (aceEngineUrl: string) => configService.updateAceEngineUrl(aceEngineUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aceEngineUrl'] });
      queryClient.invalidateQueries({ queryKey: ['allSettings'] });
    },
  });
};

/**
 * Hook for getting the rescrape interval setting
 */
export const useRescrapeInterval = () => {
  return useQuery({ queryKey: ['rescrapeInterval'], queryFn: configService.getRescrapeInterval });
};

/**
 * Hook for updating the rescrape interval setting
 */
export const useUpdateRescrapeInterval = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (hours: number) => configService.updateRescrapeInterval(hours),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rescrapeInterval'] });
      queryClient.invalidateQueries({ queryKey: ['allSettings'] });
    },
  });
};

/**
 * Hook for getting the addpid setting
 */
export const useAddPid = () => {
  return useQuery({ queryKey: ['addPid'], queryFn: configService.getAddPid });
};

/**
 * Hook for updating the addpid setting
 */
export const useUpdateAddPid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (enabled: boolean) => configService.updateAddPid(enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['addPid'] });
      queryClient.invalidateQueries({ queryKey: ['allSettings'] });
    },
  });
};

/**
 * Hook for getting all settings
 */
export const useAllSettings = () => {
  return useQuery({ queryKey: ['allSettings'], queryFn: configService.getAllSettings });
};

/**
 * Hook for checking the Acestream Engine status
 */
export const useAcestreamStatus = (options: QueryOpts<StatusResponse> = {}) => {
  return useQuery({ queryKey: ['acestreamStatus'], queryFn: configService.checkAcestreamStatus, ...options });
};

/**
 * Hook for checking system health
 */
export const useHealth = (options: QueryOpts<HealthResponse> = {}) => {
  return useQuery<HealthResponse>({ queryKey: ['health'], queryFn: configService.checkHealth, ...options });
};

/**
 * Hook for getting system statistics
 */
export const useStats = (options: QueryOpts<Stats> = {}) => {
  return useQuery<Stats>({ queryKey: ['stats'], queryFn: configService.getStats, ...options });
};

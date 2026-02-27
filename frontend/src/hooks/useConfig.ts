import { useQuery, useMutation, useQueryClient } from 'react-query';
import { configService, HealthResponse, Stats } from '../services/configService';

/**
 * Hook for getting the base URL setting
 */
export const useBaseUrl = () => {
  return useQuery('baseUrl', configService.getBaseUrl);
};

/**
 * Hook for updating the base URL setting
 */
export const useUpdateBaseUrl = () => {
  const queryClient = useQueryClient();
  return useMutation(
    (baseUrl: string) => configService.updateBaseUrl(baseUrl),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('baseUrl');
        queryClient.invalidateQueries('allSettings');
      }
    }
  );
};

/**
 * Hook for getting the Acestream Engine URL setting
 */
export const useAceEngineUrl = () => {
  return useQuery('aceEngineUrl', configService.getAceEngineUrl);
};

/**
 * Hook for updating the Acestream Engine URL setting
 */
export const useUpdateAceEngineUrl = () => {
  const queryClient = useQueryClient();
  return useMutation(
    (aceEngineUrl: string) => configService.updateAceEngineUrl(aceEngineUrl),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('aceEngineUrl');
        queryClient.invalidateQueries('allSettings');
      }
    }
  );
};

/**
 * Hook for getting the rescrape interval setting
 */
export const useRescrapeInterval = () => {
  return useQuery('rescrapeInterval', configService.getRescrapeInterval);
};

/**
 * Hook for updating the rescrape interval setting
 */
export const useUpdateRescrapeInterval = () => {
  const queryClient = useQueryClient();
  return useMutation(
    (hours: number) => configService.updateRescrapeInterval(hours),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('rescrapeInterval');
        queryClient.invalidateQueries('allSettings');
      }
    }
  );
};

/**
 * Hook for getting the addpid setting
 */
export const useAddPid = () => {
  return useQuery('addPid', configService.getAddPid);
};

/**
 * Hook for updating the addpid setting
 */
export const useUpdateAddPid = () => {
  const queryClient = useQueryClient();
  return useMutation(
    (enabled: boolean) => configService.updateAddPid(enabled),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('addPid');
        queryClient.invalidateQueries('allSettings');
      }
    }
  );
};

/**
 * Hook for getting all settings
 */
export const useAllSettings = () => {
  return useQuery('allSettings', configService.getAllSettings);
};

/**
 * Hook for checking the Acestream Engine status
 */
export const useAcestreamStatus = (options = {}) => {
  return useQuery('acestreamStatus', configService.checkAcestreamStatus, options);
};

/**
 * Hook for checking system health
 */
export const useHealth = (options = {}) => {
  return useQuery<HealthResponse>('health', configService.checkHealth, options);
};

/**
 * Hook for getting system statistics
 */
export const useStats = (options = {}) => {
  return useQuery<Stats>('stats', configService.getStats, options);
};

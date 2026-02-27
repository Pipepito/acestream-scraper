/**
 * React Query hooks for EPG
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query';
import { 
  epgService, 
  EPGSource, 
  EPGChannel, 
  EPGProgram, 
  EPGStringMapping,
  CreateEPGSourceDTO, 
  UpdateEPGSourceDTO, 
  EPGChannelMappingDTO, 
  EPGRefreshResult,
  EPGXMLGenerationParams
} from '../services/epgService';

/**
 * Hook for fetching EPG sources
 */
export const useEPGSources = (options?: UseQueryOptions<EPGSource[]>) => {
  return useQuery<EPGSource[]>(
    ['epg-sources'],
    () => epgService.getSources(),
    options
  );
};

/**
 * Hook for fetching a single EPG source
 */
export const useEPGSource = (id: number, options?: UseQueryOptions<EPGSource>) => {
  return useQuery<EPGSource>(
    ['epg-source', id],
    () => epgService.getSource(id),
    {
      enabled: !!id,
      ...options
    }
  );
};

/**
 * Hook for creating an EPG source
 */
export const useCreateEPGSource = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (sourceData: CreateEPGSourceDTO) => epgService.createSource(sourceData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('epg-sources');
      }
    }
  );
};

/**
 * Hook for updating an EPG source
 */
export const useUpdateEPGSource = (id: number) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (sourceData: UpdateEPGSourceDTO) => epgService.updateSource(id, sourceData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['epg-source', id]);
        queryClient.invalidateQueries('epg-sources');
      }
    }
  );
};

/**
 * Hook for deleting an EPG source
 */
export const useDeleteEPGSource = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: number) => epgService.deleteSource(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('epg-sources');
      }
    }
  );
};

/**
 * Hook for refreshing an EPG source
 */
export const useRefreshEPGSource = (id: number) => {
  const queryClient = useQueryClient();
  
  return useMutation<EPGRefreshResult, Error>(
    () => epgService.refreshSource(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['epg-source', id]);
        queryClient.invalidateQueries('epg-sources');
        queryClient.invalidateQueries('epg-channels');
      }
    }
  );
};

/**
 * Hook for refreshing all EPG sources
 */
export const useRefreshAllEPGSources = () => {
  const queryClient = useQueryClient();
  
  return useMutation<EPGRefreshResult[], Error>(
    () => epgService.refreshAllSources(),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('epg-sources');
        queryClient.invalidateQueries('epg-channels');
      }
    }
  );
};

/**
 * Hook for fetching EPG channels
 */
export const useEPGChannels = (sourceId?: number, options?: UseQueryOptions<EPGChannel[]>) => {
  return useQuery<EPGChannel[]>(
    sourceId ? ['epg-channels', sourceId] : ['epg-channels'],
    () => epgService.getChannels(sourceId),
    options
  );
};

/**
 * Hook for fetching a single EPG channel
 */
export const useEPGChannel = (id: number, options?: UseQueryOptions<EPGChannel>) => {
  return useQuery<EPGChannel>(
    ['epg-channel', id],
    () => epgService.getChannel(id),
    {
      enabled: !!id,
      ...options
    }
  );
};

/**
 * Hook for mapping an EPG channel to a TV channel
 */
export const useMapEPGChannel = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (mapping: EPGChannelMappingDTO) => epgService.mapChannelToTV(mapping),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('tv-channels');
      }
    }
  );
};

/**
 * Hook for removing a mapping between EPG channel and TV channel
 */
export const useUnmapEPGChannel = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ epgChannelId, tvChannelId }: { epgChannelId: number, tvChannelId: number }) => 
      epgService.unmapChannel(epgChannelId, tvChannelId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('tv-channels');
      }
    }
  );
};

/**
 * Hook for fetching EPG programs
 */
export const useEPGPrograms = (
  channelId: number, 
  startDate?: string, 
  endDate?: string,
  options?: UseQueryOptions<EPGProgram[]>
) => {
  return useQuery<EPGProgram[]>(
    ['epg-programs', channelId, startDate, endDate],
    () => epgService.getPrograms(channelId, startDate, endDate),
    {
      enabled: !!channelId,
      ...options
    }
  );
};

/**
 * Hook for fetching EPG string mappings
 */
export const useEPGStringMappings = (channelId: number, options?: UseQueryOptions<EPGStringMapping[]>) => {
  return useQuery<EPGStringMapping[]>(
    ['epg-string-mappings', channelId],
    () => epgService.getStringMappings(channelId),
    {
      enabled: !!channelId,
      ...options
    }
  );
};

/**
 * Hook for adding an EPG string mapping
 */
export const useAddEPGStringMapping = (channelId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ pattern, isExclusion }: { pattern: string, isExclusion: boolean }) => 
      epgService.addStringMapping(channelId, pattern, isExclusion),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['epg-string-mappings', channelId]);
      }
    }
  );
};

/**
 * Hook for deleting an EPG string mapping
 */
export const useDeleteEPGStringMapping = (channelId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: number) => epgService.deleteStringMapping(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['epg-string-mappings', channelId]);
      }
    }
  );
};

/**
 * Hook for generating and downloading EPG XML
 */
export const useDownloadEPGXML = () => {
  return useMutation(
    (params?: EPGXMLGenerationParams) => epgService.downloadEPGXML(params)
  );
};

/**
 * Hook for generating EPG XML URL
 */
export const useGenerateEPGXML = () => {
  return useMutation<string, Error, EPGXMLGenerationParams | undefined>(
    (params?: EPGXMLGenerationParams) => epgService.generateEPGXML(params)
  );
};

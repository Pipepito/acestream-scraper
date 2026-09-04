/**
 * React Query hooks for EPG
 */
import { useQuery, useMutation, useQueryClient, keepPreviousData, UseQueryOptions } from '@tanstack/react-query';
import {
  epgService,
  EPGSource,
  EPGChannel,
  PaginatedEPGChannels,
  EPGProgram,
  EPGStringMapping,
  CreateEPGSourceDTO,
  UpdateEPGSourceDTO,
  EPGChannelMappingDTO,
  EPGRefreshResult,
  EPGXMLGenerationParams
} from '../services/epgService';

type QueryOpts<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

/**
 * Hook for fetching EPG sources
 */
export const useEPGSources = (options?: QueryOpts<EPGSource[]>) => {
  return useQuery<EPGSource[]>({
    queryKey: ['epg-sources'],
    queryFn: () => epgService.getSources(),
    ...options,
  });
};

/**
 * Hook for fetching a single EPG source
 */
export const useEPGSource = (id: number, options?: QueryOpts<EPGSource>) => {
  return useQuery<EPGSource>({
    queryKey: ['epg-source', id],
    queryFn: () => epgService.getSource(id),
    enabled: !!id,
    ...options,
  });
};

/**
 * Hook for creating an EPG source
 */
export const useCreateEPGSource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sourceData: CreateEPGSourceDTO) => epgService.createSource(sourceData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    },
  });
};

/**
 * Hook for updating an EPG source
 */
export const useUpdateEPGSource = (id: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sourceData: UpdateEPGSourceDTO) => epgService.updateSource(id, sourceData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-source', id] });
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    },
  });
};

/**
 * Hook for deleting an EPG source
 */
export const useDeleteEPGSource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => epgService.deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    },
  });
};

/**
 * Hook for refreshing an EPG source
 */
export const useRefreshEPGSource = (id: number) => {
  const queryClient = useQueryClient();

  return useMutation<EPGRefreshResult, Error>({
    mutationFn: () => epgService.refreshSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-source', id] });
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
    },
  });
};

/**
 * Hook for refreshing all EPG sources
 */
export const useRefreshAllEPGSources = () => {
  const queryClient = useQueryClient();

  return useMutation<EPGRefreshResult[], Error>({
    mutationFn: () => epgService.refreshAllSources(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
    },
  });
};

/**
 * Hook for fetching EPG channels
 */
export const useEPGChannels = (
  sourceId?: number,
  page = 1,
  pageSize = 50,
  options?: QueryOpts<PaginatedEPGChannels>
) => {
  return useQuery<PaginatedEPGChannels>({
    queryKey: ['epg-channels', sourceId ?? 'all', page, pageSize],
    queryFn: () => epgService.getChannels(sourceId, (page - 1) * pageSize, pageSize),
    placeholderData: keepPreviousData,
    ...options,
  });
};

export const useResolveEPGChannel = (
  sourceId?: number,
  channelXmlId?: string,
  options?: QueryOpts<EPGChannel>
) => {
  return useQuery<EPGChannel>({
    queryKey: ['epg-channel-resolve', sourceId ?? 'none', channelXmlId ?? 'none'],
    queryFn: () => epgService.resolveChannel(sourceId as number, channelXmlId as string),
    enabled: !!sourceId && !!channelXmlId,
    ...options,
  });
};

/**
 * Hook for fetching a single EPG channel
 */
export const useEPGChannel = (id: number, options?: QueryOpts<EPGChannel>) => {
  return useQuery<EPGChannel>({
    queryKey: ['epg-channel', id],
    queryFn: () => epgService.getChannel(id),
    enabled: !!id,
    ...options,
  });
};

/**
 * Hook for mapping an EPG channel to a TV channel
 */
export const useMapEPGChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (mapping: EPGChannelMappingDTO) => epgService.mapChannelToTV(mapping),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tv-channels'] });
    },
  });
};

/**
 * Hook for removing a mapping between EPG channel and TV channel
 */
export const useUnmapEPGChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ epgChannelId, tvChannelId }: { epgChannelId: number, tvChannelId: number }) =>
      epgService.unmapChannel(epgChannelId, tvChannelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tv-channels'] });
    },
  });
};

/**
 * Hook for fetching EPG programs
 */
export const useEPGPrograms = (
  channelId: number,
  startDate?: string,
  endDate?: string,
  options?: QueryOpts<EPGProgram[]>
) => {
  return useQuery<EPGProgram[]>({
    queryKey: ['epg-programs', channelId, startDate, endDate],
    queryFn: () => epgService.getPrograms(channelId, startDate, endDate),
    enabled: !!channelId,
    ...options,
  });
};

/**
 * Hook for fetching EPG string mappings
 */
export const useEPGStringMappings = (channelId: number, options?: QueryOpts<EPGStringMapping[]>) => {
  return useQuery<EPGStringMapping[]>({
    queryKey: ['epg-string-mappings', channelId],
    queryFn: () => epgService.getStringMappings(channelId),
    enabled: !!channelId,
    ...options,
  });
};

export const useAllEPGStringMappings = (options?: QueryOpts<EPGStringMapping[]>) => {
  return useQuery<EPGStringMapping[]>({
    queryKey: ['epg-string-mappings', 'all'],
    queryFn: () => epgService.getAllStringMappings(),
    ...options,
  });
};

/**
 * Hook for adding an EPG string mapping
 */
export const useAddEPGStringMapping = (channelId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pattern, isExclusion }: { pattern: string, isExclusion: boolean }) =>
      epgService.addStringMapping(channelId, pattern, isExclusion),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-string-mappings', channelId] });
    },
  });
};

/**
 * Hook for deleting an EPG string mapping
 */
export const useDeleteEPGStringMapping = (channelId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => epgService.deleteStringMapping(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-string-mappings', channelId] });
    },
  });
};

export const useDeleteGlobalEPGStringMapping = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => epgService.deleteStringMapping(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-string-mappings', 'all'] });
    },
  });
};

/**
 * Hook for generating and downloading EPG XML
 */
export const useDownloadEPGXML = () => {
  return useMutation({
    mutationFn: (params?: EPGXMLGenerationParams) => epgService.downloadEPGXML(params),
  });
};

/**
 * Hook for generating EPG XML URL
 */
export const useGenerateEPGXML = () => {
  return useMutation<string, Error, EPGXMLGenerationParams | undefined>({
    mutationFn: (params?: EPGXMLGenerationParams) => epgService.generateEPGXML(params),
  });
};

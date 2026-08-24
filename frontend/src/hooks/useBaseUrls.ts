/**
 * React Query hooks for named stream base URLs (issue #62)
 *
 * Kept in its own module (separate from useConfig) so page tests that mock
 * hook modules wholesale stay valid.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import {
  baseUrlService,
  StreamBaseUrl,
  CreateBaseUrlDTO,
  UpdateBaseUrlDTO,
} from '../services/baseUrlService';

type QueryOpts<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

/**
 * Hook for fetching the named base URL list
 */
export const useBaseUrls = (options?: QueryOpts<StreamBaseUrl[]>) => {
  return useQuery<StreamBaseUrl[]>({
    queryKey: ['base-urls'],
    queryFn: () => baseUrlService.getBaseUrls(),
    ...options,
  });
};

/**
 * Hook for creating a named base URL entry
 */
export const useCreateBaseUrl = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (baseUrlData: CreateBaseUrlDTO) => baseUrlService.createBaseUrl(baseUrlData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['base-urls'] });
    },
  });
};

/**
 * Hook for patching a named base URL entry when the ID is only known at
 * call time (row edits, "make default" actions).
 */
export const usePatchBaseUrl = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateBaseUrlDTO }) => baseUrlService.updateBaseUrl(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['base-urls'] });
    },
  });
};

/**
 * Hook for deleting a named base URL entry
 */
export const useDeleteBaseUrl = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => baseUrlService.deleteBaseUrl(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['base-urls'] });
    },
  });
};

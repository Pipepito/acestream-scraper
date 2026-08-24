/**
 * React Query hooks for named stream base URLs (issue #62)
 *
 * Kept in its own module (separate from useConfig) so page tests that mock
 * hook modules wholesale stay valid.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query';
import {
  baseUrlService,
  StreamBaseUrl,
  CreateBaseUrlDTO,
  UpdateBaseUrlDTO,
} from '../services/baseUrlService';

/**
 * Hook for fetching the named base URL list
 */
export const useBaseUrls = (options?: UseQueryOptions<StreamBaseUrl[]>) => {
  return useQuery<StreamBaseUrl[]>(
    'base-urls',
    () => baseUrlService.getBaseUrls(),
    options
  );
};

/**
 * Hook for creating a named base URL entry
 */
export const useCreateBaseUrl = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (baseUrlData: CreateBaseUrlDTO) => baseUrlService.createBaseUrl(baseUrlData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('base-urls');
      }
    }
  );
};

/**
 * Hook for patching a named base URL entry when the ID is only known at
 * call time (row edits, "make default" actions).
 */
export const usePatchBaseUrl = () => {
  const queryClient = useQueryClient();

  return useMutation(
    ({ id, data }: { id: number; data: UpdateBaseUrlDTO }) => baseUrlService.updateBaseUrl(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('base-urls');
      }
    }
  );
};

/**
 * Hook for deleting a named base URL entry
 */
export const useDeleteBaseUrl = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (id: number) => baseUrlService.deleteBaseUrl(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('base-urls');
      }
    }
  );
};

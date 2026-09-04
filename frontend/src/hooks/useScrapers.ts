/**
 * React Query hooks for scrapers
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { scraperService, ScrapedURL, CreateURLDTO, UpdateURLDTO, URLFilters, ScrapeResult } from '../services/scraperService';

type QueryOpts<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

/**
 * Hook for fetching URLs list
 */
export const useURLs = (filters?: URLFilters, options?: QueryOpts<ScrapedURL[]>) => {
  return useQuery<ScrapedURL[]>({
    queryKey: ['urls', filters],
    queryFn: () => scraperService.getURLs(filters),
    ...options,
  });
};

/**
 * Hook for fetching a single URL
 */
export const useURL = (id: number, options?: QueryOpts<ScrapedURL>) => {
  return useQuery<ScrapedURL>({
    queryKey: ['url', id],
    queryFn: () => scraperService.getURL(id),
    enabled: !!id,
    ...options,
  });
};

/**
 * Hook for creating a URL
 */
export const useCreateURL = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (urlData: CreateURLDTO) => scraperService.createURL(urlData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['urls'] });
    },
  });
};

/**
 * Hook for updating a URL
 */
export const useUpdateURL = (id: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (urlData: UpdateURLDTO) => scraperService.updateURL(id, urlData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['url', id] });
      queryClient.invalidateQueries({ queryKey: ['urls'] });
    },
  });
};

/**
 * Hook for patching a URL when the ID is only known at call time
 * (e.g. inline row toggles). Invalidates the same queries as useUpdateURL.
 */
export const usePatchURL = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateURLDTO }) => scraperService.updateURL(id, data),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['url', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['urls'] });
    },
  });
};

/**
 * Hook for deleting a URL
 */
export const useDeleteURL = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => scraperService.deleteURL(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['urls'] });
    },
  });
};

/**
 * Hook for scraping a specific URL
 */
export const useScrapeURL = (id: number) => {
  const queryClient = useQueryClient();

  return useMutation<ScrapeResult, Error>({
    mutationFn: () => scraperService.scrapeURL(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['url', id] });
      queryClient.invalidateQueries({ queryKey: ['urls'] });
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });
};

/**
 * Hook for scraping all enabled URLs
 */
export const useScrapeAllURLs = () => {
  const queryClient = useQueryClient();

  return useMutation<ScrapeResult[], Error>({
    mutationFn: () => scraperService.scrapeAllURLs(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['urls'] });
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });
};

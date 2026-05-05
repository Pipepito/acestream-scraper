/**
 * React Query hooks for scrapers
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query';
import { scraperService, ScrapedURL, CreateURLDTO, UpdateURLDTO, URLFilters, ScrapeResult } from '../services/scraperService';

/**
 * Hook for fetching URLs list
 */
export const useURLs = (filters?: URLFilters, options?: UseQueryOptions<ScrapedURL[]>) => {
  return useQuery<ScrapedURL[]>(
    ['urls', filters], 
    () => scraperService.getURLs(filters),
    options
  );
};

/**
 * Hook for fetching a single URL
 */
export const useURL = (id: number, options?: UseQueryOptions<ScrapedURL>) => {
  return useQuery<ScrapedURL>(
    ['url', id],
    () => scraperService.getURL(id),
    {
      enabled: !!id,
      ...options
    }
  );
};

/**
 * Hook for creating a URL
 */
export const useCreateURL = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (urlData: CreateURLDTO) => scraperService.createURL(urlData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('urls');
      }
    }
  );
};

/**
 * Hook for updating a URL
 */
export const useUpdateURL = (id: number) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (urlData: UpdateURLDTO) => scraperService.updateURL(id, urlData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['url', id]);
        queryClient.invalidateQueries('urls');
      }
    }
  );
};

/**
 * Hook for deleting a URL
 */
export const useDeleteURL = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: number) => scraperService.deleteURL(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('urls');
      }
    }
  );
};

/**
 * Hook for scraping a specific URL
 */
export const useScrapeURL = (id: number) => {
  const queryClient = useQueryClient();
  
  return useMutation<ScrapeResult, Error>(
    () => scraperService.scrapeURL(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['url', id]);
        queryClient.invalidateQueries('urls');
        queryClient.invalidateQueries('channels');
      }
    }
  );
};

/**
 * Hook for scraping all enabled URLs
 */
export const useScrapeAllURLs = () => {
  const queryClient = useQueryClient();
  
  return useMutation<ScrapeResult[], Error>(
    () => scraperService.scrapeAllURLs(),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('urls');
        queryClient.invalidateQueries('channels');
      }
    }
  );
};

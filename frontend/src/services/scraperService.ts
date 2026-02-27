/**
 * Scraper API service
 */
import apiClient from './apiClient';

/**
 * Scraper URL model interface
 */
export interface ScrapedURL {
  id: number;
  url: string;
  url_type: string;
  enabled: boolean;
  last_processed?: string;
  error_count: number;
  last_error?: string;
  added_at: string;
  channels_found?: number;
}

/**
 * URL creation DTO
 */
export interface CreateURLDTO {
  url: string;
  url_type: string;
  enabled?: boolean;
}

/**
 * URL update DTO
 */
export interface UpdateURLDTO {
  url?: string;
  url_type?: string;
  enabled?: boolean;
}

/**
 * URL filter parameters
 */
export interface URLFilters {
  url_type?: string;
  enabled?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

/**
 * Scrape result interface
 */
export interface ScrapeResult {
  url_id: number;
  channels_found: number;
  channels_added: number;
  channels_updated: number;
  duration_seconds: number;
  success: boolean;
  error?: string;
}

/**
 * Scraper API service
 */
export const scraperService = {
  /**
   * Get all URLs
   */
  getURLs: async (filters?: URLFilters): Promise<ScrapedURL[]> => {
    const { data } = await apiClient.get('/v1/scrapers/urls', { params: filters });
    return data;
  },

  /**
   * Get a URL by ID
   */
  getURL: async (id: number): Promise<ScrapedURL> => {
    const { data } = await apiClient.get(`/v1/scrapers/urls/${id}`);
    return data;
  },

  /**
   * Create a new URL
   */
  createURL: async (urlData: CreateURLDTO): Promise<ScrapedURL> => {
    const { data } = await apiClient.post('/v1/scrapers/urls', urlData);
    return data;
  },

  /**
   * Update a URL
   */
  updateURL: async (id: number, urlData: UpdateURLDTO): Promise<ScrapedURL> => {
    const { data } = await apiClient.patch(`/v1/scrapers/urls/${id}`, urlData);
    return data;
  },

  /**
   * Delete a URL
   */
  deleteURL: async (id: number): Promise<void> => {
    await apiClient.delete(`/v1/scrapers/urls/${id}`);
  },

  /**
   * Trigger scraping of a URL
   */
  scrapeURL: async (id: number): Promise<ScrapeResult> => {
    const { data } = await apiClient.post(`/v1/scrapers/urls/${id}/scrape`);
    return data;
  },

  /**
   * Trigger scraping of all enabled URLs
   */
  scrapeAllURLs: async (): Promise<ScrapeResult[]> => {
    const { data } = await apiClient.post('/v1/scrapers/urls/scrape_all');
    return data;
  }
};

export default scraperService;

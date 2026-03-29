/**
 * API Client for interfacing with Acestream Scraper backend
 */
import axios, { AxiosInstance } from 'axios';

import { getApiBaseUrl } from '../config/runtime';
import { ApiError, normalizeApiError } from './apiErrors';

/**
 * Base API configuration
 */
const apiBase = getApiBaseUrl({
  dev: process.env.NODE_ENV === 'development',
});

const apiClient: AxiosInstance = axios.create({
  baseURL: apiBase,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Response interceptor for handling errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    throw normalizeApiError(error);
  }
);

export { ApiError };
export default apiClient;

/**
 * API Client for interfacing with Acestream Scraper backend
 */
import axios, { AxiosInstance } from 'axios';

import { getApiBaseUrl } from '../config/runtime';
import { ApiError, normalizeApiError } from './apiErrors';
import { getApiToken, reportApiTokenRequired } from './apiToken';

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
 * Request interceptor: attach the stored API token (Settings page) as an
 * X-Api-Token header when present. Only needed when the server enforces
 * the API_TOKEN env var; harmless otherwise.
 */
apiClient.interceptors.request.use((config) => {
  const token = getApiToken();
  if (token) {
    config.headers['X-Api-Token'] = token;
  }
  return config;
});

/**
 * Response interceptor for handling errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      // Server enforces an API token and this request lacked a valid one.
      reportApiTokenRequired();
    }
    throw normalizeApiError(error);
  }
);

export { ApiError };
export default apiClient;

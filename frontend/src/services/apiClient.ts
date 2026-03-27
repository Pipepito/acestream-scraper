/**
 * API Client for interfacing with Acestream Scraper backend
 */
import axios, { AxiosInstance } from 'axios';

import { ApiError, normalizeApiError } from './apiErrors';

/**
 * Base API configuration
 */
const apiBase =
  process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api'
    : '/api';

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

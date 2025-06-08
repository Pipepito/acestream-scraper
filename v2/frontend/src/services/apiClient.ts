/**
 * API Client for interfacing with Acestream Scraper backend
 */
import axios, { AxiosInstance } from 'axios';

/**
 * Base API configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Generic API error class
 */
export class ApiError extends Error {
  status: number;
  data?: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

/**
 * Response interceptor for handling errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      throw new ApiError(
        error.response.data.detail || 'An error occurred',
        error.response.status,
        error.response.data
      );
    }
    throw new ApiError('Network Error', 0);
  }
);

export default apiClient;

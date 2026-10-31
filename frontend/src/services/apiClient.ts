/**
 * API Client for interfacing with Acestream Scraper backend
 */
import axios, { AxiosInstance } from 'axios';

import { getApiBaseUrl } from '../config/runtime';
import { ApiError, normalizeApiError } from './apiErrors';
import { getApiToken, reportApiTokenRequired } from './apiToken';
import { accessSession, ACCESS_EXPIRED } from './accessSession';

/**
 * Base API configuration
 */
const apiBase = getApiBaseUrl({
  dev: process.env.NODE_ENV === 'development',
});

const apiClient: AxiosInstance = axios.create({
  baseURL: apiBase,
  withCredentials: true,
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
  const token = accessSession.managed() ? null : getApiToken();
  if (token) {
    config.headers['X-Api-Token'] = token;
  }
  if (accessSession.csrf()) config.headers['X-CSRF-Token'] = accessSession.csrf();
  return config;
});

/**
 * Response interceptor for handling errors
 */
apiClient.interceptors.response.use(
  (response) => {
    // Firefox may finish an XHR during document navigation with status 0 and an
    // empty body. Axios accepts status 0 for file URLs; our HTTP API must not.
    if (response.status === 0) throw new ApiError({ status: 0, kind: 'offline', canRetry: true,
      code: 'API_CONNECTION_INTERRUPTED', message: 'The connection was interrupted. Try again.' });
    return response;
  },
  (error) => {
    if (error?.response?.status === 401) {
      // Server enforces an API token and this request lacked a valid one.
      if (accessSession.managed()) {
        if (!error.config?.url?.endsWith('/auth/login')) window.dispatchEvent(new Event(ACCESS_EXPIRED));
      } else reportApiTokenRequired();
    }
    throw normalizeApiError(error);
  }
);

export { ApiError };
export default apiClient;

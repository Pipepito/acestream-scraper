import { ApiError, normalizeApiError } from '../services/apiErrors';

const UNKNOWN_ERROR_MESSAGE = 'Something went wrong. Try again.';

const ERROR_COPY: Record<ApiError['kind'], string> = {
  offline: 'Unable to reach the server. Check your connection and try again.',
  timeout: 'The request took too long. Try again in a moment.',
  auth: 'Your session has expired. Sign in again and retry.',
  permission: 'You do not have permission to perform this action.',
  not_found: 'The requested item could not be found.',
  validation: 'Please review the highlighted information and try again.',
  rate_limit: 'Too many requests were sent. Wait a moment and try again.',
  server: 'The server could not complete the request. Try again shortly.',
  unknown: UNKNOWN_ERROR_MESSAGE,
};

/**
 * Extract a user-friendly message from an error
 */
export const getErrorMessage = (error: unknown): string => {
  const normalizedError = normalizeApiError(error);

  // Explicit API errors carry operator-facing messages, including actionable
  // 5xx failures such as unavailable recording storage. Raw/unexpected server
  // failures still receive generic copy.
  if ((normalizedError.kind === 'validation' || (normalizedError.code && normalizedError.code !== 'INTERNAL_ERROR')) && normalizedError.message.trim()) {
    return normalizedError.message;
  }

  return ERROR_COPY[normalizedError.kind] ?? UNKNOWN_ERROR_MESSAGE;
};

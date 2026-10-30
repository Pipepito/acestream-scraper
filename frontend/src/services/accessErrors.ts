import { normalizeApiError } from './apiErrors';
import { getErrorMessage } from '../utils/errorUtils';

/** Account and Cast endpoints return curated HTTPException details for 4xx failures. */
export function getAccessErrorMessage(error: unknown): string {
  const normalized = normalizeApiError(error);
  if (normalized.status >= 400 && normalized.status < 500 && typeof normalized.message === 'string') {
    return normalized.message;
  }
  return getErrorMessage(normalized);
}

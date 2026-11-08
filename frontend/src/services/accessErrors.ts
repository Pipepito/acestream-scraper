import { getLocale } from '../i18n/locale';
import { ApiError, normalizeApiError } from './apiErrors';
import { getErrorMessage } from '../utils/errorUtils';

/** Account and Cast endpoints return curated HTTPException details for 4xx failures. */
export function getAccessErrorMessage(error: unknown): string {
  const normalized = normalizeApiError(error);
  if (normalized.code) return getErrorMessage(normalized);
  if (getLocale() === 'en-US' && normalized.status >= 400 && normalized.status < 500 && typeof normalized.message === 'string') {
    return normalized.message;
  }
  return getErrorMessage(normalized);
}

/** Capability denials carry the same stable code as the corresponding action. */
export function getCapabilityErrorMessage(value: { message?: string; error_code?: string | null }): string {
  return getAccessErrorMessage(new ApiError({ status: 403, kind: 'permission', canRetry: false,
    message: value.message ?? '', code: value.error_code ?? undefined }));
}

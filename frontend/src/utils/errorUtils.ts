import i18next from 'i18next';
import { getLocale } from '../i18n/locale';
import { normalizeApiError } from '../services/apiErrors';

/**
 * Extract a user-friendly message from an error
 */
export const getErrorMessage = (error: unknown): string => {
  const normalizedError = normalizeApiError(error);

  if (normalizedError.code && i18next.exists(normalizedError.code, { ns: 'errors', lng: 'en' })) {
    return i18next.t(normalizedError.code, { ns: 'errors', defaultValue: i18next.t('unknown', { ns: 'errors' }) });
  }
  // Legacy endpoints without reason codes retain their actionable English detail.
  // Spanish uses safe status-based guidance, never matches an English sentence.
  // Explicit API errors carry operator-facing messages, including actionable
  // 5xx failures such as unavailable recording storage. Raw/unexpected server
  // failures still receive generic copy.
  if (getLocale() === 'en-US' && normalizedError.kind === 'validation' && normalizedError.message.trim()) {
    return normalizedError.message;
  }

  return i18next.t(normalizedError.kind, { ns: 'errors' });
};

/**
 * For call sites that have always shown a failure's own text. English keeps that
 * text verbatim; other languages get translated guidance, never an English
 * sentence. Undefined when the failure is not an Error.
 */
export const getErrorDetail = (error: unknown): string | undefined => {
  if (!(error instanceof Error)) return undefined;
  return getLocale() === 'en-US' ? error.message : getErrorMessage(error);
};

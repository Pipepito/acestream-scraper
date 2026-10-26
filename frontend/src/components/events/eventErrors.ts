import { normalizeApiError } from '../../services/apiErrors';
import { getErrorMessage } from '../../utils/errorUtils';

/** Event endpoints return bounded validation locations/messages without private inputs. */
export function eventErrorMessage(error: unknown): string {
  const normalized = normalizeApiError(error);
  if (normalized.status === 409) return normalized.message;
  if (normalized.status === 422 && normalized.data && typeof normalized.data === 'object' && 'detail' in normalized.data) {
    const detail: unknown = normalized.data.detail;
    if (Array.isArray(detail)) {
      const messages = detail.slice(0, 10).flatMap((item: unknown) => {
        if (!item || typeof item !== 'object' || !('msg' in item) || typeof item.msg !== 'string') return [];
        const path = 'loc' in item && Array.isArray(item.loc) ? item.loc.filter((part: unknown) => typeof part === 'number' || typeof part === 'string').join('.') : 'Schedule';
        return [`${path}: ${item.msg}`];
      });
      if (messages.length) return messages.join('\n');
    }
  }
  return getErrorMessage(normalized);
}

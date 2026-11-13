import { getLocale } from '../../i18n/locale';
import { uiText } from '../../i18n/text';
import { ApiError,normalizeApiError } from '../../services/apiErrors';
import { getErrorMessage } from '../../utils/errorUtils';

const validationCodes: Record<string, string> = {
  missing: 'VALIDATION_REQUIRED', string_too_long: 'VALIDATION_TOO_LONG', too_long: 'VALIDATION_TOO_LONG',
  string_too_short: 'VALIDATION_TOO_SHORT', too_short: 'VALIDATION_TOO_SHORT', literal_error: 'VALIDATION_CHOICE',
  extra_forbidden: 'VALIDATION_EXTRA_FIELD', int_parsing: 'VALIDATION_NUMBER', int_type: 'VALIDATION_NUMBER',
  greater_than_equal: 'VALIDATION_NUMBER', greater_than: 'VALIDATION_NUMBER', less_than_equal: 'VALIDATION_NUMBER', less_than: 'VALIDATION_NUMBER',
  datetime_parsing: 'VALIDATION_DATETIME', datetime_from_date_parsing: 'VALIDATION_DATETIME', timezone_aware: 'VALIDATION_DATETIME',
};
const fieldLabel = (field: unknown) => {
  switch (field) {
    case 'timezone': return uiText('Timezone');
    case 'title': return uiText('Title');
    case 'starts_at': return uiText('Start');
    case 'ends_at': return uiText('End');
    case 'sport': return uiText('Sport');
    case 'competition': return uiText('Competition');
    case 'participants': return uiText('Participants');
    case 'state': return uiText('Status');
    case 'url': return uiText('URL');
    case 'headers': return uiText('Headers');
    default: return uiText('Schedule');
  }
};

/** Translate stable validation types; never inspect input, private headers or English sentences. */
export function eventErrorMessage(error: unknown): string {
  const normalized = normalizeApiError(error);
  if (normalized.status === 409 && getLocale() === 'en-US') return normalized.message;
  if (normalized.status === 422 && normalized.data && typeof normalized.data === 'object' && 'detail' in normalized.data) {
    const detail: unknown = normalized.data.detail;
    if (Array.isArray(detail)) {
      const messages = detail.slice(0, 10).flatMap((item: unknown) => {
        if (!item || typeof item !== 'object' || !('msg' in item) || typeof item.msg !== 'string') return [];
        const location = 'loc' in item && Array.isArray(item.loc) ? item.loc.filter((part: unknown) => typeof part === 'number' || typeof part === 'string') : [];
        if (getLocale() === 'en-US') return [`${location.join('.') || uiText('Schedule')}: ${item.msg}`];
        const code = 'type' in item && typeof item.type === 'string' ? validationCodes[item.type] ?? item.type : undefined;
        const message = getErrorMessage(new ApiError({ status: 422, kind: 'validation', canRetry: false, code, message: item.msg }));
        const row = location.find((part: unknown) => typeof part === 'number');
        const label = fieldLabel(location[location.length - 1]);
        return [uiText('{{field}}: {{message}}', { field: typeof row === 'number' ? uiText('Row {{row}} · {{field}}', { row: row + 1, field: label }) : label, message })];
      });
      if (messages.length) return messages.join('\n');
    }
  }
  return getErrorMessage(normalized);
}

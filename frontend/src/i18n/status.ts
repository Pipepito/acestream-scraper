import i18next from 'i18next';

/** Wire codes stay unchanged in requests, comparisons and stored data. */
export function statusLabel(code: string | null | undefined): string {
  return i18next.t(code || 'unknown', { ns: 'status', defaultValue: i18next.t('unknown', { ns: 'status' }) });
}

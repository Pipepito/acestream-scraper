import i18next, { type TFunction } from 'i18next';

/** Reads the current language on each call; never captures a language at module load. */
export const uiText: TFunction<'ui'> = i18next.getFixedT(null, 'ui');

/** Only for application-owned labels or protocol diagnostics, never catalogue data. */
export function translateKnown(message: string): string {
  return i18next.t(message, { ns: 'ui', defaultValue: message });
}

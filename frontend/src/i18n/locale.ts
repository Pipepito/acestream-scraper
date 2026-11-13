import i18next from 'i18next';

/** The chosen UI language, independently of the programme's timezone. */
export const getLocale = (): 'en-US' | 'es-ES' =>
  (i18next.resolvedLanguage ?? i18next.language)?.startsWith('es') ? 'es-ES' : 'en-US';

export const formatCount = (value: number): string => new Intl.NumberFormat(getLocale()).format(value);

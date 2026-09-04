const DATE_FALLBACK = 'Not available';
const NUMBER_FALLBACK = '0';
const FALLBACK_LOCALE = 'en-US';

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value);

const formatWithFallback = <T>(formatter: () => T, fallback: () => T): T => {
  try {
    return formatter();
  } catch (error) {
    if (error instanceof RangeError) {
      return fallback();
    }

    throw error;
  }
};

export const formatDateTime = (value?: string | null, locale?: string): string => {
  if (!value) {
    return DATE_FALLBACK;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return DATE_FALLBACK;
  }

  return formatWithFallback(
    () =>
      new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date),
    () =>
      new Intl.DateTimeFormat(FALLBACK_LOCALE, {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
  );
};

export const formatNumber = (value?: number | null, locale?: string): string => {
  if (!isFiniteNumber(value)) {
    return NUMBER_FALLBACK;
  }

  return formatWithFallback(
    () =>
      new Intl.NumberFormat(locale, {
        maximumFractionDigits: 20,
      }).format(value),
    () =>
      new Intl.NumberFormat(FALLBACK_LOCALE, {
        maximumFractionDigits: 20,
      }).format(value)
  );
};

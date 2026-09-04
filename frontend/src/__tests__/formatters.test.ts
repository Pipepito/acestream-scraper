import { formatDateTime, formatNumber } from '../utils/formatters';

describe('formatters', () => {
  it('returns a stable fallback for missing and invalid dates', () => {
    expect(formatDateTime(undefined, 'en-US')).toBe('Not available');
    expect(formatDateTime('not-a-date', 'en-US')).toBe('Not available');
  });

  it('formats dates with the requested locale', () => {
    expect(formatDateTime('2024-01-15T13:45:00Z', 'en-US')).toMatch(/2024/);
    expect(formatDateTime('2024-01-15T13:45:00Z', 'de-DE')).toMatch(/2024/);
  });

  it('falls back safely when callers pass an invalid date locale', () => {
    const originalDateTimeFormat = Intl.DateTimeFormat;
    const defaultLocaleSpy = jest
      .spyOn(Intl, 'DateTimeFormat')
      .mockImplementation(((locale?: string | string[], options?: Intl.DateTimeFormatOptions) => {
        if (locale === 'bad-locale-!') {
          throw new RangeError('Incorrect locale information provided');
        }

        if (locale === undefined) {
          return new originalDateTimeFormat('fr-FR', options);
        }

        return new originalDateTimeFormat(locale, options);
      }) as typeof Intl.DateTimeFormat);

    expect(formatDateTime('2024-01-15T13:45:00Z', 'bad-locale-!')).toMatch(/2024/);

    defaultLocaleSpy.mockRestore();
  });

  it('returns a stable numeric fallback for missing and invalid values', () => {
    expect(formatNumber(undefined, 'en-US')).toBe('0');
    expect(formatNumber(null, 'en-US')).toBe('0');
    expect(formatNumber(Number.NaN, 'en-US')).toBe('0');
    expect(formatNumber(Number.POSITIVE_INFINITY, 'en-US')).toBe('0');
  });

  it('formats large numbers with locale-aware grouping', () => {
    expect(formatNumber(1234567890, 'en-US')).toBe('1,234,567,890');
    expect(formatNumber(1234567.89, 'de-DE')).toBe('1.234.567,89');
  });

  it('falls back safely when callers pass an invalid number locale', () => {
    const originalNumberFormat = Intl.NumberFormat;
    const defaultLocaleSpy = jest
      .spyOn(Intl, 'NumberFormat')
      .mockImplementation(((locale?: string | string[], options?: Intl.NumberFormatOptions) => {
        if (locale === 'bad-locale-!') {
          throw new RangeError('Incorrect locale information provided');
        }

        if (locale === undefined) {
          return new originalNumberFormat('fr-FR', options);
        }

        return new originalNumberFormat(locale, options);
      }) as typeof Intl.NumberFormat);

    expect(formatNumber(1234567890, 'bad-locale-!')).toBe('1,234,567,890');

    defaultLocaleSpy.mockRestore();
  });
});

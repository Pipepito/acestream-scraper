import i18next from 'i18next';
import { ApiError } from '../services/apiErrors';
import { getErrorMessage } from '../utils/errorUtils';

describe('getErrorMessage', () => {
  it('turns permission failures into actionable copy', () => {
    const error = new ApiError({
      message: 'Forbidden',
      status: 403,
      kind: 'permission',
      canRetry: false,
    });

    expect(getErrorMessage(error)).toBe('You do not have permission to perform this action.');
  });

  it('turns offline failures into retry guidance', () => {
    const error = new ApiError({
      message: 'Network Error',
      status: 0,
      kind: 'offline',
      canRetry: true,
    });

    expect(getErrorMessage(error)).toContain('Check your connection');
  });

  it('preserves useful backend validation messages', () => {
    const error = new ApiError({
      message: 'Channel URL is required',
      status: 422,
      kind: 'validation',
      canRetry: false,
    });

    expect(getErrorMessage(error)).toBe('Channel URL is required');
  });

  it('normalizes raw backend-style validation errors before picking copy', () => {
    expect(
      getErrorMessage({
        isAxiosError: true,
        message: 'Request failed',
        response: {
          status: 422,
          data: {
            detail: 'Name cannot be empty',
          },
        },
      })
    ).toBe('Name cannot be empty');
  });

  it('falls back to generic unknown copy for non-error values', () => {
    expect(getErrorMessage('boom')).toBe('Something went wrong. Try again.');
  });
});

 it('preserves explicit storage errors but masks unexpected server failures', () => {
  const message = 'Recording storage is unavailable. Check the configured directory and mount.';
  const error = (code?: string) => ({ isAxiosError: true, message: 'Request failed', response: {
    status: 503, data: { error: { code, message } },
  } });
  expect(getErrorMessage(error('RECORDING_STORAGE_UNAVAILABLE'))).toBe(message);
  expect(getErrorMessage(error('INTERNAL_ERROR'))).toBe('The server could not complete the request. Try again shortly.');
  expect(getErrorMessage(error())).toBe('The server could not complete the request. Try again shortly.');
});

 describe('localized error boundaries', () => {
  afterEach(async () => { await i18next.changeLanguage('en'); });
  it('uses a stable backend code even when the backend sentence changes', async () => {
    await i18next.changeLanguage('es');
    const failure = new ApiError({ message: 'An internal sentence which must not be matched', status: 503, kind: 'server', canRetry: true, code: 'RECORDING_STORAGE_UNAVAILABLE' });
    expect(getErrorMessage(failure)).toBe(i18next.t('RECORDING_STORAGE_UNAVAILABLE', { ns: 'errors' }));
    expect(getErrorMessage(failure)).not.toMatch(/internal|Recording storage/);
  });
  it('uses localized status guidance for unknown codes and structured validation', async () => {
    await i18next.changeLanguage('es');
    expect(getErrorMessage({ isAxiosError: true, response: { status: 422, data: { detail: [{ msg: 'Field required' }] } } })).toBe(i18next.t('validation', { ns: 'errors' }));
    expect(getErrorMessage(new ApiError({ message: 'secret internal path', status: 500, kind: 'server', canRetry: true, code: 'FUTURE_CODE' }))).toBe(i18next.t('server', { ns: 'errors' }));
  });
});

describe('account and receiver HTTP error metadata', () => {
  afterEach(async () => { await i18next.changeLanguage('en'); });
  it.each(['ACCESS_CSRF_REQUIRED', 'CAST_DEVICE_NOT_FOUND', 'ACCESS_STORAGE_UNAVAILABLE'] as const)('translates %s without matching server wording', async (code) => {
    await i18next.changeLanguage('es');
    const failure = { isAxiosError: true, response: { status: 403, headers: { 'x-error-code': code }, data: { detail: 'Server wording can change' } } };
    expect(getErrorMessage(failure)).toBe(i18next.t(code, { ns: 'errors' }));
    expect(getErrorMessage(failure)).not.toContain('Server wording');
  });
});

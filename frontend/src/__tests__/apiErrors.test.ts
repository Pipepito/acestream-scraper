import type { AxiosError, InternalAxiosRequestConfig } from 'axios';

const createAxiosConfig = (): InternalAxiosRequestConfig => ({
  headers: {} as InternalAxiosRequestConfig['headers'],
} as InternalAxiosRequestConfig);

jest.mock('axios', () => {
  const instance = {
    interceptors: {
      response: {
        use: jest.fn(),
      },
    },
  };

  return {
    __esModule: true,
    default: {
      create: jest.fn(() => instance),
    },
    create: jest.fn(() => instance),
  };
});

import { ApiError, normalizeApiError } from '../services/apiErrors';
import { ApiError as ApiErrorFromClient } from '../services/apiClient';
import { ApiError as ApiErrorFromServices, normalizeApiError as normalizeApiErrorFromServices } from '../services';

const createAxiosError = (
  overrides: Partial<AxiosError> = {}
): AxiosError =>
  ({
    isAxiosError: true,
    name: 'AxiosError',
    message: 'Request failed',
    toJSON: () => ({}),
    config: createAxiosConfig(),
    ...overrides,
  } as AxiosError);

describe('normalizeApiError', () => {
  it('normalizes legacy detail payloads into validation errors', () => {
    const error = createAxiosError({
      response: {
        status: 422,
        statusText: 'Unprocessable Entity',
        headers: {},
        config: createAxiosConfig(),
        data: {
          detail: 'Channel URL is required',
        },
      },
    });

    const normalized = normalizeApiError(error);

    expect(normalized).toBeInstanceOf(ApiError);
    expect(normalized.message).toBe('Channel URL is required');
    expect(normalized.kind).toBe('validation');
    expect(normalized.status).toBe(422);
    expect(normalized.canRetry).toBe(false);
    expect(normalized.code).toBeUndefined();
    expect(normalized.correlationId).toBeUndefined();
  });

  it('normalizes structured backend envelopes with metadata', () => {
    const error = createAxiosError({
      response: {
        status: 429,
        statusText: 'Too Many Requests',
        headers: {},
        config: createAxiosConfig(),
        data: {
          error: {
            code: 'RATE_LIMITED',
            message: 'Too many refresh attempts',
            correlation_id: 'corr-123',
            context: {
              retry_after_seconds: 60,
            },
          },
        },
      },
    });

    const normalized = normalizeApiError(error);

    expect(normalized.message).toBe('Too many refresh attempts');
    expect(normalized.kind).toBe('rate_limit');
    expect(normalized.status).toBe(429);
    expect(normalized.canRetry).toBe(true);
    expect(normalized.code).toBe('RATE_LIMITED');
    expect(normalized.correlationId).toBe('corr-123');
    expect(normalized.context).toEqual({ retry_after_seconds: 60 });
  });

  it('categorizes network connectivity issues as offline', () => {
    const normalized = normalizeApiError(
      createAxiosError({
        code: 'ERR_NETWORK',
        message: 'Network Error',
        request: {},
      })
    );

    expect(normalized.kind).toBe('offline');
    expect(normalized.status).toBe(0);
    expect(normalized.canRetry).toBe(true);
    expect(normalized.message).toBe('Unable to reach the server. Check your connection and try again.');
  });

  it('categorizes timeout failures separately from offline errors', () => {
    const normalized = normalizeApiError(
      createAxiosError({
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded',
      })
    );

    expect(normalized.kind).toBe('timeout');
    expect(normalized.status).toBe(0);
    expect(normalized.canRetry).toBe(true);
    expect(normalized.message).toBe('The request took too long. Please try again.');
  });

  it('maps status codes to auth, permission, not found, validation, server, and unknown kinds', () => {
    const cases = [
      { status: 401, expectedKind: 'auth' },
      { status: 403, expectedKind: 'permission' },
      { status: 404, expectedKind: 'not_found' },
      { status: 400, expectedKind: 'validation' },
      { status: 503, expectedKind: 'server' },
      { status: 418, expectedKind: 'unknown' },
    ] as const;

    for (const testCase of cases) {
      const normalized = normalizeApiError(
        createAxiosError({
          response: {
            status: testCase.status,
            statusText: 'Error',
            headers: {},
            config: createAxiosConfig(),
            data: {},
          },
        })
      );

      expect(normalized.kind).toBe(testCase.expectedKind);
      expect(normalized.status).toBe(testCase.status);
      expect(normalized.canRetry).toBe(
        testCase.expectedKind === 'server'
      );
    }
  });

  it('keeps existing ApiError instances unchanged', () => {
    const original = new ApiError({
      message: 'Already normalized',
      status: 401,
      kind: 'auth',
      canRetry: false,
      code: 'AUTH_REQUIRED',
    });

    expect(normalizeApiError(original)).toBe(original);
  });

  it('preserves the ApiError prototype chain for runtime instanceof checks', () => {
    const normalized = new ApiError({
      message: 'Missing channel',
      status: 404,
      kind: 'not_found',
      canRetry: false,
    });

    expect(normalized instanceof ApiError).toBe(true);
    expect(normalized instanceof Error).toBe(true);
  });

  it('exposes the compatibility exports from apiClient and services barrel', () => {
    expect(ApiErrorFromClient).toBe(ApiError);
    expect(ApiErrorFromServices).toBe(ApiError);
    expect(normalizeApiErrorFromServices).toBe(normalizeApiError);
  });

  it('re-exports the status helper from the services barrel', async () => {
    const services = await import('../services');

    expect(services.getApiErrorKindFromStatus(429)).toBe('rate_limit');
  });
});

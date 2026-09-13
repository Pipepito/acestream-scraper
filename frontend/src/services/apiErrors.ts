import type { AxiosError } from 'axios';

export type ApiErrorKind =
  | 'offline'
  | 'timeout'
  | 'auth'
  | 'permission'
  | 'not_found'
  | 'validation'
  | 'rate_limit'
  | 'server'
  | 'unknown';

type ApiErrorOptions = {
  message: string;
  status: number;
  kind: ApiErrorKind;
  canRetry: boolean;
  code?: string;
  correlationId?: string;
  context?: unknown;
  data?: unknown;
};

type BackendEnvelope = {
  error?: {
    code?: string;
    message?: string;
    correlation_id?: string;
    context?: unknown;
  };
  detail?: string;
};

export class ApiError extends Error {
  status: number;
  kind: ApiErrorKind;
  canRetry: boolean;
  code?: string;
  correlationId?: string;
  context?: unknown;
  data?: unknown;

  constructor({
    message,
    status,
    kind,
    canRetry,
    code,
    correlationId,
    context,
    data,
  }: ApiErrorOptions) {
    super(message);
    Object.setPrototypeOf(this, ApiError.prototype);
    this.name = 'ApiError';
    this.status = status;
    this.kind = kind;
    this.canRetry = canRetry;
    this.code = code;
    this.correlationId = correlationId;
    this.context = context;
    this.data = data;
  }
}

const RETRYABLE_KINDS: Record<ApiErrorKind, boolean> = {
  offline: true,
  timeout: true,
  auth: false,
  permission: false,
  not_found: false,
  validation: false,
  rate_limit: true,
  server: true,
  unknown: false,
};

const DEFAULT_MESSAGES: Record<ApiErrorKind, string> = {
  offline: 'Unable to reach the server. Check your connection and try again.',
  timeout: 'The request took too long. Please try again.',
  auth: 'Please sign in again to continue.',
  permission: 'You do not have permission to perform this action.',
  not_found: 'The requested resource could not be found.',
  validation: 'Please review the highlighted information and try again.',
  rate_limit: 'Too many requests were sent. Please wait a moment and try again.',
  server: 'The server encountered an error. Please try again shortly.',
  unknown: 'An unexpected error occurred.',
};

export const getApiErrorKindFromStatus = (status: number): ApiErrorKind => {
  switch (status) {
    case 400:
      return 'validation';
    case 401:
      return 'auth';
    case 403:
      return 'permission';
    case 404:
      return 'not_found';
    case 422:
      return 'validation';
    case 429:
      return 'rate_limit';
    default:
      if (status >= 500) {
        return 'server';
      }
      return 'unknown';
  }
};

const isAxiosLikeError = (error: unknown): error is AxiosError =>
  Boolean(error && typeof error === 'object' && (error as AxiosError).isAxiosError);

const isTimeoutError = (error: AxiosError): boolean =>
  error.code === 'ECONNABORTED' || error.message.toLowerCase().includes('timeout');

const getResponsePayload = (error: AxiosError): BackendEnvelope => {
  const data = error.response?.data;
  if (data && typeof data === 'object') {
    return data as BackendEnvelope;
  }

  return {};
};

export const normalizeApiError = (error: unknown): ApiError => {
  if (error instanceof ApiError) {
    return error;
  }

  if (isAxiosLikeError(error)) {
    if (isTimeoutError(error)) {
      return new ApiError({
        message: DEFAULT_MESSAGES.timeout,
        status: 0,
        kind: 'timeout',
        canRetry: true,
      });
    }

    if (error.code === 'ERR_NETWORK' || (!error.response && error.request)) {
      return new ApiError({
        message: DEFAULT_MESSAGES.offline,
        status: 0,
        kind: 'offline',
        canRetry: true,
      });
    }

    const status = error.response?.status ?? 0;
    const payload = getResponsePayload(error);
    const backendError = payload.error;
    const kind = getApiErrorKindFromStatus(status);
    const message =
      backendError?.message ?? payload.detail ?? DEFAULT_MESSAGES[kind];

    return new ApiError({
      message,
      status,
      kind,
      canRetry: RETRYABLE_KINDS[kind],
      code: backendError?.code,
      correlationId: backendError?.correlation_id,
      context: backendError?.context,
      data: error.response?.data,
    });
  }

  if (error instanceof Error) {
    return new ApiError({
      message: error.message || DEFAULT_MESSAGES.unknown,
      status: 0,
      kind: 'unknown',
      canRetry: false,
    });
  }

  return new ApiError({
    message: DEFAULT_MESSAGES.unknown,
    status: 0,
    kind: 'unknown',
    canRetry: false,
  });
};

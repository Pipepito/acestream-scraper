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

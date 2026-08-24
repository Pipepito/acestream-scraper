import {
  API_TOKEN_REQUIRED_EVENT,
  API_TOKEN_STORAGE_KEY,
  clearApiToken,
  getApiToken,
  isApiTokenRequired,
  reportApiTokenRequired,
  resetApiTokenRequired,
  setApiToken,
} from '../services/apiToken';

describe('apiToken storage helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    resetApiTokenRequired();
  });

  it('stores and reads the token via the apiToken localStorage key', () => {
    expect(getApiToken()).toBeNull();

    setApiToken('secret-token');

    expect(localStorage.getItem(API_TOKEN_STORAGE_KEY)).toBe('secret-token');
    expect(getApiToken()).toBe('secret-token');
  });

  it('clears the stored token', () => {
    setApiToken('secret-token');

    clearApiToken();

    expect(getApiToken()).toBeNull();
    expect(localStorage.getItem(API_TOKEN_STORAGE_KEY)).toBeNull();
  });
});

describe('apiToken 401 signalling', () => {
  beforeEach(() => {
    resetApiTokenRequired();
  });

  it('marks the token as required and can be reset', () => {
    expect(isApiTokenRequired()).toBe(false);

    reportApiTokenRequired();
    expect(isApiTokenRequired()).toBe(true);

    resetApiTokenRequired();
    expect(isApiTokenRequired()).toBe(false);
  });

  it('dispatches the required event at most once per session', () => {
    const listener = jest.fn();
    window.addEventListener(API_TOKEN_REQUIRED_EVENT, listener);

    try {
      // Use an isolated module instance so the once-per-session guard starts
      // fresh regardless of what earlier tests reported.
      jest.isolateModules(() => {
        const freshApiToken = require('../services/apiToken') as typeof import('../services/apiToken');

        freshApiToken.reportApiTokenRequired();
        freshApiToken.reportApiTokenRequired();
        freshApiToken.reportApiTokenRequired();
      });

      expect(listener).toHaveBeenCalledTimes(1);
    } finally {
      window.removeEventListener(API_TOKEN_REQUIRED_EVENT, listener);
    }
  });
});

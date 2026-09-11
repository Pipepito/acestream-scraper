/**
 * API token storage and 401 signalling helpers.
 *
 * The backend optionally requires a token when the API_TOKEN env var is set.
 * The SPA keeps the token in localStorage (key: "apiToken") and sends it as
 * an `X-Api-Token` header on every API request (see apiClient.ts).
 *
 * All localStorage access is wrapped so environments without storage
 * (SSR, some test setups, locked-down browsers) never crash.
 */

export const API_TOKEN_STORAGE_KEY = 'apiToken';
export const API_TOKEN_REQUIRED_EVENT = 'acestream:api-token-required';

const getLocalStorage = (): Storage | null => {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return null;
    }
    return window.localStorage;
  } catch {
    return null;
  }
};

/**
 * Read the stored API token, or null when unset/unavailable.
 */
export const getApiToken = (): string | null => {
  try {
    return getLocalStorage()?.getItem(API_TOKEN_STORAGE_KEY) ?? null;
  } catch {
    return null;
  }
};

/**
 * Persist the API token for future requests.
 */
export const setApiToken = (token: string): void => {
  try {
    getLocalStorage()?.setItem(API_TOKEN_STORAGE_KEY, token);
  } catch {
    // Storage unavailable (private mode, quota, SSR) - token stays unset.
  }
};

/**
 * Remove the stored API token.
 */
export const clearApiToken = (): void => {
  try {
    getLocalStorage()?.removeItem(API_TOKEN_STORAGE_KEY);
  } catch {
    // Storage unavailable - nothing to clear.
  }
};

let apiTokenRequired = false;
let apiTokenNotified = false;

/**
 * True once any API call in this session has been rejected with a 401,
 * so the Settings page can highlight the API token field.
 */
export const isApiTokenRequired = (): boolean => apiTokenRequired;

/**
 * Reset the 401 marker after the user saves or clears a token.
 */
export const resetApiTokenRequired = (): void => {
  apiTokenRequired = false;
};

/**
 * Record that the server requires an API token. Dispatches the
 * API_TOKEN_REQUIRED_EVENT browser event at most once per session so the
 * global snackbar fires a single notification even when many parallel
 * queries fail at the same time.
 */
export const reportApiTokenRequired = (): void => {
  apiTokenRequired = true;

  if (apiTokenNotified) {
    return;
  }
  apiTokenNotified = true;

  try {
    if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
      window.dispatchEvent(new CustomEvent(API_TOKEN_REQUIRED_EVENT));
    }
  } catch {
    // Non-browser environment - nothing to notify.
  }
};

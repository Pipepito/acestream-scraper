import { useCallback, useState } from 'react';
import { useUiText } from '../i18n/useUiText';

export type SnackbarSeverity = 'success' | 'error' | 'warning' | 'info';
export type SnackbarMessage = string | (() => string);
export type SnackbarNotify = (message: SnackbarMessage, severity: SnackbarSeverity) => void;
export const resolveSnackbarMessage = (message: SnackbarMessage) => typeof message === 'function' ? message() : message;
export interface SnackbarState { open: boolean; message: string; severity: SnackbarSeverity }

/** Keep the outcome and lifetime stable; resolve its wording in the current language. */
export const useSnackbar = () => {
  useUiText();
  const [state, setState] = useState<{ open: boolean; message: SnackbarMessage; severity: SnackbarSeverity }>({ open: false, message: '', severity: 'success' });
  const showSnackbar = useCallback<SnackbarNotify>((message, severity) => { setState({ open: true, message, severity }); }, []);
  const closeSnackbar = useCallback(() => { setState(previous => ({ ...previous, open: false })); }, []);
  const snackbar: SnackbarState = { ...state, message: resolveSnackbarMessage(state.message) };
  return { snackbar, showSnackbar, closeSnackbar };
};

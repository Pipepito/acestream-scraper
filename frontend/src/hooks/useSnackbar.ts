import { useState } from 'react';

export type SnackbarSeverity = 'success' | 'error' | 'warning' | 'info';

export interface SnackbarState {
  open: boolean;
  message: string;
  severity: SnackbarSeverity;
}

/**
 * Hook owning transient snackbar notification state for a page.
 */
export const useSnackbar = () => {
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    message: '',
    severity: 'success'
  });

  const showSnackbar = (message: string, severity: SnackbarSeverity) => {
    setSnackbar({
      open: true,
      message,
      severity
    });
  };

  const closeSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return { snackbar, showSnackbar, closeSnackbar };
};

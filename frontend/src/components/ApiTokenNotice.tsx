import React, { useEffect, useState } from 'react';
import { Alert, Snackbar } from '@mui/material';
import { API_TOKEN_REQUIRED_EVENT } from '../services/apiToken';

/**
 * Global, dismissible notification shown when an API call is rejected with
 * a 401 (server enforces the API_TOKEN env var and no valid token is stored).
 *
 * The apiClient response interceptor dispatches API_TOKEN_REQUIRED_EVENT at
 * most once per session, so this fires a single snackbar even when many
 * parallel queries fail together. The token itself is entered in Settings.
 */
const ApiTokenNotice: React.FC = () => {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.addEventListener !== 'function') {
      return undefined;
    }

    const handleTokenRequired = () => setOpen(true);
    window.addEventListener(API_TOKEN_REQUIRED_EVENT, handleTokenRequired);
    return () => window.removeEventListener(API_TOKEN_REQUIRED_EVENT, handleTokenRequired);
  }, []);

  const handleClose = (_event?: unknown, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpen(false);
  };

  return (
    <Snackbar
      open={open}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert onClose={() => setOpen(false)} severity="warning" variant="filled" sx={{ width: '100%' }}>
        API token required — set it in Settings
      </Alert>
    </Snackbar>
  );
};

export default ApiTokenNotice;

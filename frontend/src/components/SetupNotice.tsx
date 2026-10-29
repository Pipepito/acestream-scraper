import React, { useEffect, useState } from 'react';
import { Alert, Button } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { setupQueryKey, setupService } from '../services/setupService';

const Setup = React.lazy(() => import('../pages/Setup'));

export default function SetupNotice() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get, staleTime: 60_000, retry: false });
  useEffect(() => {
    // The explicit setup route owns its own modal. Do not reopen an automatic
    // one when the operator postpones setup from that route.
    if (pathname === '/setup') { setDismissed(true); setOpen(false); return; }
    if (query.data?.setup_complete === false && !dismissed && pathname !== '/setup') setOpen(true);
  }, [query.data?.setup_complete, dismissed, pathname]);
  if (pathname === '/setup' || !query.data) return null;
  if (open) return <React.Suspense fallback={<p role="status">Loading setup…</p>}>
    <Setup onClose={() => { setOpen(false); setDismissed(true); }} />
  </React.Suspense>;
  if (query.data.setup_complete && !query.data.restart_required) return null;
  return <Alert severity="info" sx={{ mb: 2 }} action={<Button component={Link} to="/setup" color="inherit">{query.data.restart_required ? 'Review setup' : 'Set up scraper'}</Button>}>
    {query.data.restart_required ? 'Configuration saved. Restart the container or application to apply it.' : 'Finish setup to save your deployment settings. You can return to it from Settings.'}
  </Alert>;
}

import React, { useEffect, useState } from 'react';
import { flushSync } from 'react-dom';
import { Alert, Box, Button, Typography } from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { accessService } from '../../services/accessService';
import { ACCESS_EXPIRED } from '../../services/accessSession';
import { AccessContext } from './AccessContext';
import AccountSetup from './AccountSetup';
import LoginForm from './LoginForm';
const Watch = React.lazy(() => import('../../pages/Watch'));

export default function AccessGate({ children }: { children: React.ReactNode }) {
  const cache = useQueryClient();
  const [expired, setExpired] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const query = useQuery({ queryKey: ['access-status'], queryFn: accessService.status, retry: false, staleTime: 15000, refetchOnWindowFocus: true });
  const { refetch } = query;
  const refresh = async () => {
    // Unmount protected query observers before clearing their data. Otherwise
    // they can immediately refetch with a just-revoked cookie during logout or
    // when account protection is disabled.
    flushSync(() => setRefreshing(true));
    try {
      await cache.cancelQueries();
      cache.removeQueries({ predicate: item => item.queryKey[0] !== 'access-status' });
      setExpired(false);
      await query.refetch();
    } finally { setRefreshing(false); }
  };
  useEffect(() => {
    const onExpired = () => { flushSync(() => setExpired(true)); void cache.cancelQueries().then(() => { cache.removeQueries({ predicate: item => item.queryKey[0] !== 'access-status' }); void refetch(); }); };
    window.addEventListener(ACCESS_EXPIRED, onExpired);
    return () => window.removeEventListener(ACCESS_EXPIRED, onExpired);
  }, [cache, refetch]);
  if (refreshing || !query.data || query.isError) return <Box sx={{ p: 3 }}>{query.isError ? <Alert severity="error">Access information could not be loaded. <Button onClick={() => void query.refetch()}>Retry</Button></Alert> : <Typography role="status">Checking access…</Typography>}</Box>;
  const status = query.data;
  return <AccessContext.Provider value={{ status, refresh }}>
    {status.mode === 'pending' ? <Box sx={{ p: { xs: 2, sm: 4 }, maxWidth: 760, mx: 'auto' }}><AccountSetup /></Box>
      : expired ? <Box sx={{ p: 3 }}><LoginForm /></Box>
      : status.mode === 'accounts' && !status.user?.administrator ? <React.Suspense fallback={<Typography role="status">Loading viewing page…</Typography>}><Watch key={status.user?.id ?? 'public'} /></React.Suspense>
      : children}
  </AccessContext.Provider>;
}

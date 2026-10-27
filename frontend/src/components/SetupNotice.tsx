import React from 'react';
import { Alert, Button } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { setupQueryKey, setupService } from '../services/setupService';

export default function SetupNotice() {
  const { pathname } = useLocation();
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get, staleTime: 60_000, retry: false });
  if (pathname === '/setup' || !query.data || (query.data.setup_complete && !query.data.restart_required)) return null;
  return <Alert severity="info" sx={{ mb: 2 }} action={<Button component={Link} to="/setup" color="inherit">{query.data.restart_required ? 'Review setup' : 'Set up scraper'}</Button>}>
    {query.data.restart_required ? 'Configuration saved. Restart the container or application to apply it.' : 'Choose playback and network settings, then add your first source.'}
  </Alert>;
}

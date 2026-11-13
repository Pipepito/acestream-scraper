import React from 'react';
import { Alert, Button, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import RuntimeSetup from './RuntimeSetup';
import { setupQueryKey, setupService } from '../services/setupService';

export default function SystemRuntime() {
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get });
  const navigate = useNavigate();
  const { t } = useTranslation();
  if (query.isError) return <Alert severity="error" action={<Button onClick={() => void query.refetch()}>{t('retry')}</Button>}>{t('pageFailed')}</Alert>;
  if (!query.data) return <Typography role="status">{t('loading')}</Typography>;
  return <RuntimeSetup initial={query.data} onClose={() => navigate('/system')} />;
}

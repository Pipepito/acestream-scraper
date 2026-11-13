import React from 'react';
import { Alert, Button, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

function LoadFailure() {
  const { t } = useTranslation();
  return <Alert severity="error" action={<Button onClick={() => window.location.reload()}>{t('retry')}</Button>}>{t('pageFailed')}</Alert>;
}
class PageErrorBoundary extends React.Component<{ children: React.ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <LoadFailure /> : this.props.children; }
}
export default function RouteBoundary({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  return <PageErrorBoundary><React.Suspense fallback={<Typography role="status" tabIndex={-1}>{t('loadingPage')}</Typography>}>{children}</React.Suspense></PageErrorBoundary>;
}

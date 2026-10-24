import React from 'react';
import { Alert, Link } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { currentRelease } from '../data/changelog';
import { markChangelogRead, useChangelogUnread } from '../hooks/useChangelog';

export default function WhatsNewNotice() {
  const unread = useChangelogUnread();
  const { pathname } = useLocation();
  if (!unread || pathname === '/changelog') return null;
  return (
    <Alert severity="info" onClose={markChangelogRead} closeText="Dismiss changelog notice" sx={{ mb: 2 }}>
      <Link component={RouterLink} to="/changelog" color="inherit" onClick={markChangelogRead}>
        What’s new in {currentRelease.version}
      </Link>
      {' — Read the changes included in this build.'}
    </Alert>
  );
}

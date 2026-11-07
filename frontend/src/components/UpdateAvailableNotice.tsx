import React, { useEffect, useState } from 'react';
import { Alert, AlertTitle, Link } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { systemService } from '../services/systemService';

const SEEN_KEY = 'acestream.published-update.seen.v1';
const shownThisSession = new Set<string>();

/** Once per published version/browser, including when storage is unavailable. */
export default function UpdateAvailableNotice() {
  const [visibleVersion, setVisibleVersion] = useState<string | null>(null);
  const { data } = useQuery({
    queryKey: ['published-release'], queryFn: systemService.getUpdates,
    staleTime: 6 * 60 * 60 * 1000, refetchInterval: 6 * 60 * 60 * 1000,
    refetchOnWindowFocus: false, retry: false,
  });
  useEffect(() => {
    const version = data?.latest_version;
    if (!data?.update_available || !version || shownThisSession.has(version)) return;
    try {
      if (localStorage.getItem(SEEN_KEY) === version) return;
      localStorage.setItem(SEEN_KEY, version);
    } catch { /* In-memory fallback for browsers that deny storage. */ }
    shownThisSession.add(version);
    setVisibleVersion(version);
  }, [data]);
  if (!visibleVersion || !data?.update_available || visibleVersion !== data.latest_version) return null;
  return (
    <Alert severity="info" onClose={() => setVisibleVersion(null)} closeText="Dismiss new version notice" sx={{ mb: 2 }}>
      <AlertTitle>{visibleVersion} is available</AlertTitle>
      {data.deployment === 'docker'
        ? 'To update, pull the new Docker image and recreate your container with your existing configuration and volumes.'
        : 'To update, download the latest release and update your installation yourself.'}
      {' The app does not update itself. '}
      <Link href={`https://github.com/Pipepito/acestream-scraper/releases/tag/${encodeURIComponent(visibleVersion)}`} target="_blank" rel="noopener noreferrer" color="inherit">
        View release notes and downloads (opens in a new tab)
      </Link>
    </Alert>
  );
}
